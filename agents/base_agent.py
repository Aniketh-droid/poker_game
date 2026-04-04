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

    def observe(self, opponent_action: str) -> None:
        """Optional: observe opponent's action for belief updates."""
        pass

    def reset(self) -> None:
        """Optional: reset state between hands."""
        pass
