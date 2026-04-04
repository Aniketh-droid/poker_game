"""
Game state for heads-up No-Limit Texas Hold'em.
Pure environment logic: apply_action, advance_street, is_terminal, resolve_showdown, clone.
"""

import copy
from typing import List, Any, Optional, Dict

from engine.cards import Card
from engine.action_space import (
    FOLD, CHECK, CALL, BET_25, BET_50, BET_100, ALL_IN,
    BB, get_legal_actions,
)


class GameState:
    """
    Stores: stacks, pot, street, board, private_cards, current_player,
    betting_history, raises_this_street, last_bet_size, terminal_flag.
    """

    def __init__(
        self,
        stacks: List[float],
        pot: float = 0.0,
        street: int = 0,
        board: Optional[List[Card]] = None,
        private_cards: Optional[Dict[int, List[Card]]] = None,
        current_player: int = 0,
        betting_history: Optional[List[Dict]] = None,
        raises_this_street: int = 0,
        last_bet_size: float = 0.0,
        terminal_flag: bool = False,
        street_bets: Optional[List[float]] = None,
        folded: Optional[int] = None,
    ):
        self.stacks = list(stacks)
        self.pot = pot
        self.street = street
        self.board = list(board) if board else []
        self.private_cards = dict(private_cards) if private_cards else {0: [], 1: []}
        self.current_player = current_player
        self.betting_history = list(betting_history) if betting_history else []
        self.raises_this_street = raises_this_street
        self.last_bet_size = last_bet_size
        self.terminal_flag = terminal_flag
        self.street_bets = list(street_bets) if street_bets is not None else [0.0, 0.0]
        self.folded = folded  # player_id who folded, or None
        self.to_call = 0.0  # set before get_legal_actions

    def _update_to_call(self) -> None:
        """Set to_call for current player."""
        pid = self.current_player
        self.to_call = self.street_bets[1 - pid] - self.street_bets[pid]
        if self.to_call < 0:
            self.to_call = 0.0

    def apply_action(self, action: str) -> None:
        """Apply one action; update stacks, pot, street_bets, raises, current_player, terminal."""
        if self.terminal_flag:
            return
        pid = self.current_player
        my_stack = self.stacks[pid]
        self._update_to_call()

        if action == FOLD:
            self.terminal_flag = True
            self.folded = pid
            # Winner is 1 - pid; they get the pot
            return

        if action == CHECK:
            if self.to_call != 0:
                raise ValueError("Cannot check when there is a bet to call")
            self.betting_history.append({"player_id": pid, "action": CHECK, "amount": 0, "street": self.street})
            self.current_player = 1 - pid
            # If we're back to the first aggressor and both checked this street, advance
            self._check_advance_after_check(pid)
            return

        if action == CALL:
            amount = min(my_stack, self.to_call)
            self.stacks[pid] -= amount
            self.pot += amount
            self.street_bets[pid] += amount
            self.betting_history.append({"player_id": pid, "action": CALL, "amount": amount, "street": self.street})
            self.last_bet_size = 0.0
            self.current_player = 1 - pid
            self._check_advance_after_call()
            return

        # Bet/raise sizes: 25%, 50%, 100% pot, or all-in
        pot_after_call = self.pot + self.to_call if self.to_call > 0 else self.pot
        if action == BET_25:
            amount = min(my_stack, max(BB, round(pot_after_call * 0.25, 2)))
        elif action == BET_50:
            amount = min(my_stack, max(BB, round(pot_after_call * 0.5, 2)))
        elif action == BET_100:
            amount = min(my_stack, max(BB, round(pot_after_call * 1.0, 2)))
        elif action == ALL_IN:
            amount = my_stack
        else:
            raise ValueError(f"Unknown action: {action}")

        if amount <= 0:
            raise ValueError("Bet/raise amount must be positive")

        self.stacks[pid] -= amount
        self.pot += amount
        self.street_bets[pid] += amount
        self.raises_this_street += 1
        self.last_bet_size = amount - self.street_bets[1 - pid]  # raise over opponent's current bet
        if self.last_bet_size < 0:
            self.last_bet_size = amount
        self.betting_history.append({"player_id": pid, "action": action, "amount": amount, "street": self.street})
        self.current_player = 1 - pid
        self._update_to_call()
        return

    def _check_advance_after_check(self, who_checked: int) -> None:
        """If both players have acted and last was check, advance street or end hand."""
        # After a check, it's opponent's turn. If opponent already checked this street, we advance.
        n_checks = sum(1 for e in self.betting_history if e.get("action") == CHECK and e.get("street") == self.street)
        n_acts = sum(1 for e in self.betting_history if e.get("street") == self.street)
        if n_acts >= 2 and n_checks >= 2:
            self.advance_street()

    def _check_advance_after_call(self) -> None:
        """After a call, if we're at end of street (both put in same this street), advance."""
        if self.street_bets[0] == self.street_bets[1]:
            self.advance_street()

    def advance_street(self) -> None:
        """Move to next street; reset street_bets and raises_this_street. If river done, terminal."""
        self.street += 1
        self.street_bets = [0.0, 0.0]
        self.raises_this_street = 0
        self.last_bet_size = 0.0
        self.current_player = 0
        if self.street > 3:
            self.terminal_flag = True

    def is_terminal(self) -> bool:
        """True if hand is over (fold, all-in resolved, or end of river)."""
        return self.terminal_flag

    def resolve_showdown(
        self, evaluator: Any
    ) -> List[float]:
        """
        Resolve showdown with given hand evaluator.
        Returns chip delta for each player (e.g. [delta0, delta1]).
        """
        if self.folded is not None:
            winner = 1 - self.folded
            deltas = [0.0, 0.0]
            deltas[winner] = self.pot
            deltas[self.folded] = 0.0
            return deltas

        hand0 = self.private_cards.get(0, []) + self.board
        hand1 = self.private_cards.get(1, []) + self.board
        if len(hand0) < 5 or len(hand1) < 5:
            # Split pot if no full hand
            half = self.pot / 2.0
            return [half, half]
        cmp = evaluator.compare(hand0, hand1)
        if cmp > 0:
            return [self.pot, 0.0]
        if cmp < 0:
            return [0.0, self.pot]
        half = self.pot / 2.0
        return [half, half]

    def clone(self) -> "GameState":
        """Deep copy of state."""
        return copy.deepcopy(self)
