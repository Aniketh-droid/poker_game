"""
Tight agent: rule-based. Play premium hands, fold weak, rare bluff. No Monte Carlo.
"""

from typing import Any

from agents.base_agent import BaseAgent
from engine.action_space import get_legal_actions, FOLD, CHECK, CALL, BET_25, BET_50, BET_100, ALL_IN
from belief.hand_bucketing import classify_preflop, classify_postflop, PREMIUM, STRONG, MEDIUM, SPECULATIVE, TRASH


class TightAgent(BaseAgent):
    def __init__(self, player_id: int = 0):
        self.player_id = player_id

    def act(self, game_state: Any) -> str:
        legal = get_legal_actions(game_state, self.player_id)
        if not legal:
            return FOLD
        hand = game_state.private_cards.get(self.player_id, [])
        board = getattr(game_state, "board", [])
        if len(board) < 3:
            bucket = classify_preflop(hand)
        else:
            bucket = classify_postflop(hand, board)

        if bucket == PREMIUM:
            if BET_100 in legal:
                return BET_100
            if BET_50 in legal:
                return BET_50
            if BET_25 in legal:
                return BET_25
            if ALL_IN in legal and len(legal) <= 3:
                return ALL_IN
            if CALL in legal:
                return CALL
            return CHECK if CHECK in legal else legal[0]
        if bucket == STRONG:
            if CALL in legal and CHECK not in legal:
                return CALL
            if CHECK in legal:
                return CHECK
            if BET_25 in legal:
                return BET_25
            return legal[0]
        if bucket == MEDIUM:
            if CHECK in legal:
                return CHECK
            if CALL in legal:
                return CALL
            if FOLD in legal:
                return FOLD
            return legal[0]
        if bucket == SPECULATIVE or bucket == TRASH:
            if CHECK in legal:
                return CHECK
            if FOLD in legal:
                return FOLD
            if CALL in legal:
                return CALL
            return legal[0]

        if "STRONG" in bucket or "PREMIUM" in bucket:
            if BET_50 in legal:
                return BET_50
            if CALL in legal:
                return CALL
            return CHECK if CHECK in legal else legal[0]
        if "WEAK" in bucket or "AIR" in bucket:
            if CHECK in legal:
                return CHECK
            if FOLD in legal:
                return FOLD
            return legal[0]
        if CHECK in legal:
            return CHECK
        if CALL in legal:
            return CALL
        return legal[0]
