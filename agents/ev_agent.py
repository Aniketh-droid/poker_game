"""
EV agent: Monte Carlo equity, uniform belief, no Bayesian update.
"""

import random
from typing import Any

from agents.base_agent import BaseAgent
from engine.action_space import get_legal_actions
from decision.ev_calculator import compute_ev
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

    def act(self, game_state: Any) -> str:
        legal = get_legal_actions(game_state, self.player_id)
        if not legal:
            self._hand_actions.append("FOLD")
            return "FOLD"
        ev_dict = {}
        for action in legal:
            ev_dict[action] = compute_ev(
                action, game_state, belief=None, hero_id=self.player_id,
                samples=self.samples, rng=self._rng,
            )
        chosen = select_action(ev_dict, legal, epsilon=self.epsilon, rng=self._rng)
        self._last_ev_dict = ev_dict
        self._hand_actions.append(chosen)
        return chosen
