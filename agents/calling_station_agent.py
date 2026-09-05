"""
Calling Station agent ("Calling Station"): loose-passive, rule-based, no Monte Carlo.

Almost never folds and almost never raises -- just calls, and calls, and calls.
The mirror image of ManiacAgent: where the Maniac's aggression barely depends on
hand strength, the Calling Station's *passivity* barely depends on hand strength
either. A great value target (bet it and it pays you off) and a terrible bluff
target (it doesn't fold, so don't bother).
"""

import random
from typing import Any

from agents.base_agent import BaseAgent
from engine.action_space import get_legal_actions, FOLD, CHECK, CALL, BET_25, BET_50, BET_100, ALL_IN
from belief.hand_bucketing import classify_preflop, classify_postflop, PREMIUM, STRONG_MADE, STRONG_DRAW


class CallingStationAgent(BaseAgent):
    def __init__(self, player_id: int = 0, seed: int = None, fold_chance: float = 0.03):
        self.player_id = player_id
        self._rng = random.Random(seed)
        # Even a calling station occasionally lays one down -- but it's rare and
        # doesn't depend much on how bad the hand actually is, which is the joke.
        self.fold_chance = fold_chance

    def _bucket(self, game_state: Any) -> str:
        hand = game_state.private_cards.get(self.player_id, [])
        board = getattr(game_state, "board", [])
        if len(board) < 3:
            return classify_preflop(hand)
        return classify_postflop(hand, board)

    def act(self, game_state: Any) -> str:
        legal = get_legal_actions(game_state, self.player_id)
        if not legal:
            return FOLD

        bucket = self._bucket(game_state)
        very_strong = bucket in (PREMIUM, STRONG_MADE, STRONG_DRAW)

        can_check = CHECK in legal
        can_call = CALL in legal
        can_fold = FOLD in legal
        can_bet = any(a in legal for a in (BET_25, BET_50, BET_100, ALL_IN))

        if can_check:
            # Only bets out with a genuinely strong hand, and even then rarely --
            # a real calling station's whole game is letting others do the betting.
            if very_strong and can_bet and self._rng.random() < 0.12:
                for a in (BET_25, BET_50):
                    if a in legal:
                        return a
            return CHECK

        if can_call:
            if can_fold and self._rng.random() < self.fold_chance:
                return FOLD
            return CALL

        if can_fold:
            return FOLD
        return legal[0]
