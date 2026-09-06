"""
Bayesian agent ("The Profiler"): maintains one belief distribution PER LIVE OPPONENT,
updates each independently on that opponent's actions, and picks actions by EV against
whichever opponents are still live -- heads-up (the original 2-player benchmark) or at
a 3-6 handed table.

FIXES (heads-up, still in effect):
1. _last_street was read from self inside _Ctx via getattr(self,...) but _Ctx doesn't
   capture self -- it always returned street 0. Fixed by passing street directly.
2. Belief transition preflop->postflop now carries forward signal by mapping the
   preflop posterior into a postflop prior instead of resetting to uniform.
3. observe() now correctly passes street from game_state rather than a stale field.

MULTIWAY: observe()/act() were originally written around a single implicit opponent.
Generalized here to key every piece of per-opponent state (belief, empirical fold/call
stats, postflop-transition flag) by actor_id (seat number), so "the Rock raised" and
"the Maniac raised" update separate models instead of being conflated into one stream.
At exactly one live opponent (the original heads-up case) this reduces to using
decision.ev_calculator.compute_ev exactly as before -- same code path, same behavior,
so the already-verified heads-up benchmark numbers are unaffected. With 2+ live
opponents it switches to decision.ev_calculator.compute_ev_multiway.
"""

import random
from typing import Any, Dict, List, Optional

from agents.base_agent import BaseAgent
from engine.action_space import get_legal_actions
from decision.ev_calculator import compute_ev, compute_ev_multiway
from decision.strategy_mixer import select_action
from belief.hand_bucketing import (
    classify_preflop, classify_postflop,
    PREMIUM, STRONG, MEDIUM, SPECULATIVE, TRASH,
    STRONG_MADE, MEDIUM_MADE, WEAK_MADE, STRONG_DRAW, WEAK_DRAW, AIR,
)
from belief.bayesian_update import update_belief
from belief.entropy import compute_entropy
from belief.opponent_stats import OpponentStats, blend_with_prior
from belief.opponent_model import get_fold_probability

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

        # All per-opponent state is keyed by actor_id (seat number). At a heads-up
        # table there's exactly one key; at a 3-6 handed table there's one per live
        # opponent, each tracked completely independently.
        self._beliefs: Dict[int, Dict[str, float]] = {}
        self._transitioned: Dict[int, bool] = {}
        # Empirical fold/call tracking per opponent, accumulated across the whole
        # match. Deliberately NOT touched by reset(): belief is a per-hand quantity
        # (what are this opponent's hole cards right now?) but opponent_stats answers
        # a cross-hand question (how does this opponent actually behave?) and needs
        # many hands of signal to be useful -- see belief/opponent_stats.py.
        self._opponent_stats: Dict[int, OpponentStats] = {}

        self._entropy_history: List[float] = []
        self._hand_actions: List[str] = []
        self._last_street: int = 0

    def _get_or_init(self, actor_id: int) -> Dict[str, float]:
        if actor_id not in self._beliefs:
            self._beliefs[actor_id] = _uniform_prior(PREFLOP_BUCKETS)
            self._transitioned[actor_id] = False
        if actor_id not in self._opponent_stats:
            self._opponent_stats[actor_id] = OpponentStats()
        return self._beliefs[actor_id]

    def reset(self) -> None:
        # Belief and the postflop-transition flag are per-hand; reset every opponent
        # we've seen so far back to a fresh uniform prior. opponent_stats persists.
        for key in list(self._beliefs.keys()):
            self._beliefs[key] = _uniform_prior(PREFLOP_BUCKETS)
            self._transitioned[key] = False
        self._entropy_history = []
        self._hand_actions = []
        self._last_street = 0

    def observe(self, opponent_action: str, street: int = 0, actor_id: int = None) -> None:
        """
        Update the belief for whichever opponent took this action.
        `actor_id` is required to tell opponents apart at a multiway table; a legacy
        caller that omits it (shouldn't happen via the real engine anymore) falls
        back to a single generic opponent bucket, keyed 0.
        """
        key = actor_id if actor_id is not None else 0
        belief = self._get_or_init(key)

        class _Ctx:
            pass
        ctx = _Ctx()
        ctx.street = street  # FIX: was getattr(self, '_last_street', 0) via class attr

        belief = update_belief(
            belief,
            opponent_action,
            ctx,
            opponent_type=self.opponent_type,
        )
        self._opponent_stats[key].record(opponent_action, street)

        if self.forgetting_factor > 0:
            keys = list(belief.keys())
            uniform = 1.0 / len(keys) if keys else 0.0
            mixed = {
                k: (1.0 - self.forgetting_factor) * belief[k] + self.forgetting_factor * uniform
                for k in keys
            }
            s = sum(mixed.values())
            if s > 0:
                belief = {k: v / s for k, v in mixed.items()}

        self._beliefs[key] = belief

    def _maybe_transition_to_postflop(self, board: list) -> None:
        """
        Transition every currently-tracked opponent's belief from preflop to postflop
        bucket space once the board appears (each opponent transitions independently,
        the first time we see a flop-or-later board this hand).
        """
        if len(board) < 3:
            return
        for key, belief in list(self._beliefs.items()):
            if not self._transitioned.get(key, False):
                self._beliefs[key] = _board_aware_transition(belief, board, rng=self._rng)
                self._transitioned[key] = True

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

    def _live_opponents(self, game_state: Any) -> List[int]:
        if hasattr(game_state, "live_players"):
            return [i for i in game_state.live_players() if i != self.player_id]
        # Legacy/plain test doubles without live_players(): assume heads-up.
        return [1 - self.player_id]

    def act(self, game_state: Any) -> str:
        self._last_street = game_state.street
        board = getattr(game_state, "board", [])
        live_opponents = self._live_opponents(game_state)

        for opp in live_opponents:
            self._get_or_init(opp)

        # Carry forward each tracked opponent's preflop posterior into a postflop prior.
        self._maybe_transition_to_postflop(board)

        legal = get_legal_actions(game_state, self.player_id)
        if not legal:
            return "FOLD"

        ev_dict = {}
        if len(live_opponents) <= 1:
            # Heads-up (or only one live opponent at a bigger table): identical to the
            # original, already-benchmarked single-opponent EV path.
            opp = live_opponents[0] if live_opponents else None
            belief = self._beliefs.get(opp, _uniform_prior(PREFLOP_BUCKETS)) if opp is not None else {}
            stats = self._opponent_stats.get(opp) if opp is not None else None
            for action in legal:
                ev_dict[action] = compute_ev(
                    action, game_state, belief=belief, hero_id=self.player_id,
                    samples=self.samples, rng=self._rng, opponent_stats=stats,
                )
        else:
            opponent_beliefs = {opp: self._beliefs.get(opp, {}) for opp in live_opponents}
            opponent_fold_probs = {}
            for opp in live_opponents:
                belief = opponent_beliefs[opp]
                prior_fold = get_fold_probability(belief, game_state) if belief else 0.2
                stats = self._opponent_stats.get(opp)
                empirical = stats.empirical_rates(game_state.street) if stats else None
                fold_prob, _ = blend_with_prior(prior_fold, 1.0 - prior_fold, empirical)
                opponent_fold_probs[opp] = fold_prob
            for action in legal:
                ev_dict[action] = compute_ev_multiway(
                    action, game_state, hero_id=self.player_id,
                    opponent_beliefs=opponent_beliefs, opponent_fold_probs=opponent_fold_probs,
                    samples=self.samples, rng=self._rng,
                )

        # Gate exploration on how confident we are about opponents' hands (average
        # entropy across every live opponent's belief).
        live_beliefs = [self._beliefs[opp] for opp in live_opponents if opp in self._beliefs]
        entropy = (
            sum(compute_entropy(b) for b in live_beliefs) / len(live_beliefs)
            if live_beliefs else 0.0
        )
        effective_epsilon = self._belief_gated_epsilon(entropy)

        chosen = select_action(ev_dict, legal, epsilon=effective_epsilon, rng=self._rng)

        self._last_ev_dict = ev_dict
        self._last_entropy = entropy
        # Exposed for the post-hand decision-rationale panel (decision/rationale.py).
        self._last_num_opponents = len(live_opponents)

        self._entropy_history.append(entropy)
        self._hand_actions.append(chosen)
        return chosen
