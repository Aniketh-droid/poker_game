"""
Maniac agent ("The Maniac"): loose-aggressive, rule-based, no Monte Carlo.

Bets and raises constantly regardless of hand strength -- weak hands get bluffed
just as often as strong ones get bet for value -- and almost never folds. High
variance by design: it's meant to punish timid opponents and occasionally get
punished itself, which is the point of a "fun" bot roster rather than a pure EV
optimizer. Genuinely different control flow from TightAgent (inverted: aggression
is close to hand-strength-independent here, where TightAgent's whole strategy IS
hand strength) rather than just a re-tuned copy of it.
"""

import random
from typing import Any

from agents.base_agent import BaseAgent
from engine.action_space import get_legal_actions, FOLD, CHECK, CALL, BET_25, BET_50, BET_100, ALL_IN
from belief.hand_bucketing import classify_preflop, classify_postflop, TRASH, SPECULATIVE, AIR, WEAK_DRAW


class ManiacAgent(BaseAgent):
    def __init__(self, player_id: int = 0, seed: int = None, aggression: float = 0.75):
        self.player_id = player_id
        self._rng = random.Random(seed)
        # Probability of betting/raising when there's a choice at all -- deliberately
        # high and only weakly dependent on hand strength (a real maniac bluffs the
        # nuts and air about the same amount, unlike every other agent in the roster).
        self.aggression = aggression

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
        # Even the maniac backs off a hair with the absolute worst holdings, just
        # enough to not be a pure coinflip machine -- but the gap to a strong hand
        # is small on purpose.
        weak = bucket in (TRASH, AIR, WEAK_DRAW, SPECULATIVE)
        fire_prob = self.aggression - (0.15 if weak else 0.0)
        # Exposed for the post-hand decision-rationale panel (decision/rationale.py).
        self._last_bucket = bucket
        self._last_fire_prob = fire_prob

        bet_actions = [a for a in (ALL_IN, BET_100, BET_50, BET_25) if a in legal]
        can_check = CHECK in legal
        can_call = CALL in legal
        can_fold = FOLD in legal

        if self._rng.random() < fire_prob and bet_actions:
            # Skew toward the biggest bets available -- maniacs overbet.
            weights = {ALL_IN: 0.35, BET_100: 0.4, BET_50: 0.2, BET_25: 0.05}
            pool = [(a, weights.get(a, 0.1)) for a in bet_actions]
            total = sum(w for _, w in pool)
            r = self._rng.uniform(0, total)
            for a, w in pool:
                r -= w
                if r <= 0:
                    return a
            return bet_actions[0]

        if can_call:
            # Rarely folds -- only lays down a genuinely bad hand facing action
            # often enough to not be a pure calling station.
            if can_fold and weak and self._rng.random() < 0.2:
                return FOLD
            return CALL
        if can_check:
            return CHECK
        if can_fold:
            return FOLD
        return legal[0]
