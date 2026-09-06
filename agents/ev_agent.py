"""
EV agent ("The Mathematician"): Monte Carlo equity, uniform belief (no opponent
modeling), no Bayesian update -- pure pot-odds/EV play.

MULTIWAY: compute_ev()'s to_call math hardcodes a heads-up opponent index
(`street_bets[1 - pid]`), which at a 3-6 handed table silently reads the wrong
seat's bet (or, via Python's negative indexing, a seat that isn't even an
opponent) instead of raising -- a quiet correctness bug, not a crash, which is
worse. With 2+ live opponents this now takes the same fork BayesianAgent uses:
decision.ev_calculator.compute_ev_multiway, with every opponent's belief left
as None (sampled uniformly -- EVAgent never tracks opponent tendencies, on or
off the two-player table) and default 0.2 fold probabilities. At exactly one
live opponent it still uses the original compute_ev() path unchanged, so the
already-benchmarked heads-up behavior is untouched.
"""

import random
from typing import Any

from agents.base_agent import BaseAgent
from engine.action_space import get_legal_actions
from decision.ev_calculator import compute_ev, compute_ev_multiway
from decision.strategy_mixer import select_action


class EVAgent(BaseAgent):
    def __init__(self, player_id: int = 0, epsilon: float = 0.05, samples: int = 200, seed: int = None):
        self.player_id = player_id
        self.epsilon = epsilon
        self.samples = samples
        self._rng = random.Random(seed)
        self._hand_actions = []

    def reset(self) -> None:
        self._hand_actions = []

    def _live_opponents(self, game_state: Any):
        if hasattr(game_state, "live_players"):
            return [i for i in game_state.live_players() if i != self.player_id]
        return [1 - self.player_id]

    def act(self, game_state: Any) -> str:
        legal = get_legal_actions(game_state, self.player_id)
        if not legal:
            self._hand_actions.append("FOLD")
            return "FOLD"

        live_opponents = self._live_opponents(game_state)
        ev_dict = {}
        if len(live_opponents) <= 1:
            for action in legal:
                ev_dict[action] = compute_ev(
                    action, game_state, belief=None, hero_id=self.player_id,
                    samples=self.samples, rng=self._rng,
                )
        else:
            opponent_beliefs = {opp: None for opp in live_opponents}
            for action in legal:
                ev_dict[action] = compute_ev_multiway(
                    action, game_state, hero_id=self.player_id,
                    opponent_beliefs=opponent_beliefs, opponent_fold_probs=None,
                    samples=self.samples, rng=self._rng,
                )

        chosen = select_action(ev_dict, legal, epsilon=self.epsilon, rng=self._rng)
        self._last_ev_dict = ev_dict
        # Exposed for the post-hand decision-rationale panel (decision/rationale.py).
        self._last_num_opponents = len(live_opponents)
        self._hand_actions.append(chosen)
        return chosen
