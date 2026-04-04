"""
Random agent: chooses random legal action.
"""

import random
from typing import Any

from agents.base_agent import BaseAgent
from engine.action_space import get_legal_actions


class RandomAgent(BaseAgent):
    def __init__(self, player_id: int = 0, rng: random.Random = None):
        self.player_id = player_id
        self._rng = rng or random.Random()

    def act(self, game_state: Any) -> str:
        legal = get_legal_actions(game_state, self.player_id)
        return self._rng.choice(legal)
