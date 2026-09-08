"""
Tight agent: rule-based. Play premium hands, fold weak, rare bluff. No Monte Carlo.
"""

from typing import Any

from agents.base_agent import BaseAgent
from engine.action_space import get_legal_actions, FOLD, CHECK, CALL, BET_25, BET_50, BET_100, ALL_IN
from belief.hand_bucketing import (
    classify, PREMIUM, STRONG, MEDIUM, SPECULATIVE, TRASH,
    STRONG_MADE, STRONG_DRAW, MEDIUM_MADE, WEAK_MADE, WEAK_DRAW, AIR,
)

# Ordered action preference per bucket -- the first legal action in the tuple wins,
# falling back to legal[0] if none are legal. Replaces two overlapping dispatch
# paths (an exact-equality chain for the 5 preflop buckets, then a substring-match
# fallback -- "STRONG" in bucket, "WEAK" in bucket -- that every postflop bucket
# actually fell through to) with one table covering all 11 buckets explicitly.
_ACTION_PREFS = {
    PREMIUM: (BET_100, BET_50, BET_25, CALL, CHECK),  # ALL_IN case handled in act()
    STRONG: (CHECK, CALL, BET_25),
    MEDIUM: (CHECK, CALL, FOLD),
    SPECULATIVE: (CHECK, FOLD, CALL),
    TRASH: (CHECK, FOLD, CALL),
    STRONG_MADE: (BET_50, CALL, CHECK),
    STRONG_DRAW: (BET_50, CALL, CHECK),
    MEDIUM_MADE: (CHECK, CALL),
    WEAK_MADE: (CHECK, FOLD),
    WEAK_DRAW: (CHECK, FOLD),
    AIR: (CHECK, FOLD),
}


class TightAgent(BaseAgent):
    def __init__(self, player_id: int = 0):
        self.player_id = player_id

    def act(self, game_state: Any) -> str:
        legal = get_legal_actions(game_state, self.player_id)
        if not legal:
            return FOLD
        hand = game_state.private_cards.get(self.player_id, [])
        board = getattr(game_state, "board", [])
        bucket = classify(hand, board)
        # Exposed for the post-hand decision-rationale panel (decision/rationale.py) --
        # not used by the decision logic itself, just a record of what it computed.
        self._last_bucket = bucket

        if bucket == PREMIUM and ALL_IN in legal and len(legal) <= 3:
            # Only shove when few actions are legal at all (e.g. a short stack with
            # no smaller bet size on the table) -- bigger sized bets above already
            # win out over an all-in whenever they're available.
            candidates = (BET_100, BET_50, BET_25, ALL_IN, CALL, CHECK)
        else:
            candidates = _ACTION_PREFS.get(bucket, (CHECK, CALL))

        for action in candidates:
            if action in legal:
                return action
        return legal[0]
