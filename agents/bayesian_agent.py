"""
Bayesian agent: maintain belief distribution, update on opponent action, EV with belief, strategy_mixer, track entropy.

FIXES:
1. _last_street was read from self inside _Ctx via getattr(self,...) but _Ctx doesn't
   capture self — it always returned street 0. Fixed by passing street directly.
2. Belief transition preflop->postflop now carries forward signal by mapping the
   preflop posterior into a postflop prior instead of resetting to uniform.
3. observe() now correctly passes street from game_state rather than a stale field.
"""

import random
from typing import Any, Dict, List

from agents.base_agent import BaseAgent
from engine.action_space import get_legal_actions
from decision.ev_calculator import compute_ev
from decision.strategy_mixer import select_action
from belief.hand_bucketing import (
    classify_preflop, classify_postflop,
    PREMIUM, STRONG, MEDIUM, SPECULATIVE, TRASH,
    STRONG_MADE, MEDIUM_MADE, WEAK_MADE, STRONG_DRAW, WEAK_DRAW, AIR,
)
from belief.bayesian_update import update_belief
from belief.entropy import compute_entropy

PREFLOP_BUCKETS = [PREMIUM, STRONG, MEDIUM, SPECULATIVE, TRASH]
POSTFLOP_BUCKETS = [STRONG_MADE, MEDIUM_MADE, WEAK_MADE, STRONG_DRAW, WEAK_DRAW, AIR]


def _uniform_prior(buckets: List[str]) -> Dict[str, float]:
    n = len(buckets)
    return {b: 1.0 / n for b in buckets}


_PREFLOP_HANDS_CACHE = None

def _get_preflop_cache():
    global _PREFLOP_HANDS_CACHE
    if _PREFLOP_HANDS_CACHE is None:
        from engine.cards import build_deck
        deck = build_deck()
        _PREFLOP_HANDS_CACHE = {b: [] for b in PREFLOP_BUCKETS}
        import itertools
        for h in itertools.combinations(deck, 2):
            b = classify_preflop(list(h))
            if b in _PREFLOP_HANDS_CACHE:
                _PREFLOP_HANDS_CACHE[b].append(list(h))
    return _PREFLOP_HANDS_CACHE

def _board_aware_transition(preflop_belief: Dict[str, float], board: List[Any], rng=None) -> Dict[str, float]:
    """
    Board-aware transition: Samples valid hands from each preflop bucket,
    evaluates them against the actual board, and weights to build the postflop prior.
    """
    if rng is None:
        rng = random.Random()
        
    cache = _get_preflop_cache()
    postflop_prior = {pb: 0.0 for pb in POSTFLOP_BUCKETS}
    
    board_strs = {str(c) for c in board}
    
    for pre_b, weight in preflop_belief.items():
        if weight < 0.001:
            continue
            
        valid_hands = [h for h in cache[pre_b] if str(h[0]) not in board_strs and str(h[1]) not in board_strs]
        if not valid_hands:
            continue
            
        # Sample max 50 hands to keep computational time low
        samples = valid_hands if len(valid_hands) <= 50 else rng.sample(valid_hands, 50)
        
        post_counts = {pb: 0 for pb in POSTFLOP_BUCKETS}
        for h in samples:
            post_b = classify_postflop(h, board)
            if post_b in post_counts:
                post_counts[post_b] += 1
                 
        for pb, count in post_counts.items():
            postflop_prior[pb] += weight * (count / len(samples))
            
    # Normalize postflop prior
    s = sum(postflop_prior.values())
    if s > 0:
        return {k: v / s for k, v in postflop_prior.items()}
    return _uniform_prior(POSTFLOP_BUCKETS)


class BayesianAgent(BaseAgent):
    def __init__(
        self,
        player_id: int = 0,
        epsilon: float = 0.05,
        samples: int = 200,
        seed: int = None,
        opponent_type: str = "TIGHT",
        forgetting_factor: float = 0.0,
    ):
        self.player_id = player_id
        self.epsilon = epsilon
        self.samples = samples
        self._rng = random.Random(seed)
        self.opponent_type = opponent_type
        self.forgetting_factor = max(0.0, min(0.25, forgetting_factor))
        self._belief: Dict[str, float] = _uniform_prior(PREFLOP_BUCKETS)
        self._entropy_history: List[float] = []
        self._hand_actions: List[str] = []
        self._last_street: int = 0
        self._transitioned_to_postflop: bool = False

    def reset(self) -> None:
        self._belief = _uniform_prior(PREFLOP_BUCKETS)
        self._entropy_history = []
        self._hand_actions = []
        self._last_street = 0
        self._transitioned_to_postflop = False

    def observe(self, opponent_action: str, street: int = 0) -> None:
        """
        Update belief given opponent action and current street.
        Street is now passed explicitly to avoid the stale _last_street bug.
        """
        class _Ctx:
            pass
        ctx = _Ctx()
        ctx.street = street  # FIX: was getattr(self, '_last_street', 0) via class attr

        self._belief = update_belief(
            self._belief,
            opponent_action,
            ctx,
            opponent_type=self.opponent_type,
        )

        if self.forgetting_factor > 0:
            keys = list(self._belief.keys())
            uniform = 1.0 / len(keys) if keys else 0.0
            mixed = {
                k: (1.0 - self.forgetting_factor) * self._belief[k] + self.forgetting_factor * uniform
                for k in keys
            }
            s = sum(mixed.values())
            if s > 0:
                self._belief = {k: v / s for k, v in mixed.items()}

    def _maybe_transition_to_postflop(self, board: list) -> None:
        """
        Transition from preflop to postflop belief space when the board appears.
        Uses _board_aware_transition to evaluate bucket mapping accurately per board texture.
        """
        if not self._transitioned_to_postflop and len(board) >= 3:
            self._belief = _board_aware_transition(self._belief, board, rng=self._rng)
            self._transitioned_to_postflop = True

    def _belief_gated_epsilon(self, entropy: float) -> float:
        """
        Scale exploration (epsilon) based on current belief entropy.

        High entropy (>1.2) = still uncertain = allow normal exploration (bluffing ok).
        Low entropy (<0.5)  = confident about opponent = suppress bluffs entirely.
        Linear interpolation in between.

        Max entropy for 6 postflop buckets = ln(6) ≈ 1.79
        Max entropy for 5 preflop buckets  = ln(5) ≈ 1.61
        """
        HIGH_ENTROPY = 1.2   # above this: full epsilon
        LOW_ENTROPY  = 0.5   # below this: near-zero epsilon
        MIN_EPSILON  = 0.005 # floor so agent isn't fully deterministic

        if entropy >= HIGH_ENTROPY:
            return self.epsilon
        if entropy <= LOW_ENTROPY:
            return MIN_EPSILON
        # Linear interpolation
        t = (entropy - LOW_ENTROPY) / (HIGH_ENTROPY - LOW_ENTROPY)
        return MIN_EPSILON + t * (self.epsilon - MIN_EPSILON)

    def act(self, game_state: Any) -> str:
        self._last_street = game_state.street
        board = getattr(game_state, "board", [])

        # Carry forward preflop posterior into postflop prior on flop
        self._maybe_transition_to_postflop(board)

        legal = get_legal_actions(game_state, self.player_id)
        if not legal:
            return "FOLD"

        ev_dict = {}
        for action in legal:
            ev_dict[action] = compute_ev(
                action, game_state, belief=self._belief, hero_id=self.player_id,
                samples=self.samples, rng=self._rng,
            )

        # Gate exploration on how confident we are about opponent's hand
        entropy = compute_entropy(self._belief)
        effective_epsilon = self._belief_gated_epsilon(entropy)

        chosen = select_action(ev_dict, legal, epsilon=effective_epsilon, rng=self._rng)
        
        self._last_ev_dict = ev_dict
        self._last_entropy = entropy
        
        self._entropy_history.append(entropy)
        self._hand_actions.append(chosen)
        return chosen