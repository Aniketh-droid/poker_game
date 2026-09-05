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

    def observe(self, opponent_action: str, street: int = 0, actor_id: int = None) -> None:
        """Optional: observe an opponent's action for belief updates.

        `street` is the street the action was actually taken on (passed by
        engine.game_engine.play_hand/play_hand_multiway). `actor_id` is which
        seat took the action -- required at a multiway table (3+ players) so a
        per-opponent belief model can tell "the Rock raised" apart from "the
        Maniac raised" instead of conflating every opponent into one stream.
        At a 2-handed table actor_id is always the sole opponent and may be
        omitted by legacy callers. Subclasses that don't care about opponent
        actions (RandomAgent, EVAgent, TightAgent, HumanAgent) can ignore both;
        BayesianAgent uses them to index its per-opponent likelihood/belief state.
        """
        pass

    def reset(self) -> None:
        """Optional: reset state between hands."""
        pass
