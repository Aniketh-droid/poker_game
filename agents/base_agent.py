"""
Abstract base agent: act(game_state), observe(opponent_action), reset().
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    """Abstract base for all agents."""

    @abstractmethod
    def act(self, game_state: Any) -> str:
        """Return one legal action given current game state."""
        pass

    def observe(self, opponent_action: str, street: int = 0) -> None:
        """Optional: observe opponent's action for belief updates.

        `street` is the street the action was actually taken on (passed by
        engine.game_engine.play_hand). Subclasses that don't care about the
        opponent's actions (RandomAgent, EVAgent, TightAgent, HumanAgent) can
        ignore it; BayesianAgent uses it to index the correct row of its
        opponent-model likelihood tables.
        """
        pass

    def reset(self) -> None:
        """Optional: reset state between hands."""
        pass
