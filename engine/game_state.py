"""
Game state for N-handed (2-6 players) No-Limit Texas Hold'em.
Pure environment logic: apply_action, advance_street, is_terminal, resolve_showdown, clone.

Generalized from a hardcoded 2-player implementation to a configurable table size
(num_players inferred from len(stacks)). At num_players == 2 this reduces exactly to
the original heads-up behavior (button acts first preflop, same street-closing rule),
so the existing heads-up benchmark/tests keep working unmodified.

Key differences from the heads-up version:
- folded is a set (any number of players can fold), not a single player id.
- all_in tracks players who have committed their whole stack and can no longer act.
- street_bets/private_cards/stacks are length-N.
- total_contributed tracks each player's total chips put into the pot across the whole
  hand (blinds + every street), needed to compute side pots when stacks differ and
  someone goes all-in for less than another player.
- button rotates seat-to-seat across hands (game_engine.py increments it); action order
  is button-relative instead of hardcoded to player 0/1.
"""

import copy
from typing import List, Any, Optional, Dict, Set

from engine.cards import Card
from engine.action_space import (
    FOLD, CHECK, CALL, BET_25, BET_50, BET_100, ALL_IN,
    BB,
)


class GameState:
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
        folded: Optional[Any] = None,
        all_in: Optional[Any] = None,
        button: int = 0,
        acted_this_street: Optional[Any] = None,
        total_contributed: Optional[List[float]] = None,
    ):
        self.stacks = list(stacks)
        self.num_players = len(self.stacks)
        self.pot = pot
        self.street = street
        self.board = list(board) if board else []
        self.private_cards = dict(private_cards) if private_cards else {i: [] for i in range(self.num_players)}
        self.current_player = current_player
        self.betting_history = list(betting_history) if betting_history else []
        self.raises_this_street = raises_this_street
        self.last_bet_size = last_bet_size
        self.terminal_flag = terminal_flag
        self.street_bets = list(street_bets) if street_bets is not None else [0.0] * self.num_players

        # folded/all_in accept either a set, a single legacy int (old 2-player callers
        # passed folded=<player_id> or None), or None.
        if folded is None:
            self.folded: Set[int] = set()
        elif isinstance(folded, int):
            self.folded = {folded}
        else:
            self.folded = set(folded)

        self.all_in: Set[int] = set(all_in) if all_in else set()
        self.button = button
        self.acted_this_street: Set[int] = set(acted_this_street) if acted_this_street else set()
        self.total_contributed = list(total_contributed) if total_contributed is not None else [0.0] * self.num_players
        self.to_call = 0.0  # set before get_legal_actions

    # ---- player-set helpers ------------------------------------------------

    def live_players(self) -> List[int]:
        """Players who haven't folded (still eligible to win the pot)."""
        return [i for i in range(self.num_players) if i not in self.folded]

    def actionable_players(self) -> List[int]:
        """Live players who still have chips and aren't all-in -- i.e. can still act."""
        return [i for i in self.live_players() if i not in self.all_in and self.stacks[i] > 1e-9]

    # ---- action application -------------------------------------------------

    def _update_to_call(self) -> None:
        pid = self.current_player
        live = self.live_players()
        max_bet = max((self.street_bets[i] for i in live), default=0.0)
        self.to_call = max(0.0, max_bet - self.street_bets[pid])

    def _commit(self, pid: int, amount: float) -> None:
        """Move `amount` chips from player pid's stack into the pot."""
        amount = min(amount, self.stacks[pid])
        self.stacks[pid] -= amount
        self.pot += amount
        self.street_bets[pid] += amount
        self.total_contributed[pid] += amount
        if self.stacks[pid] <= 1e-9:
            self.all_in.add(pid)

    def apply_action(self, action: str) -> None:
        """Apply one action; update stacks, pot, street_bets, raises, current_player, terminal."""
        if self.terminal_flag:
            return
        pid = self.current_player
        my_stack = self.stacks[pid]
        self._update_to_call()
        self.acted_this_street.add(pid)

        if action == FOLD:
            self.folded.add(pid)
            self.betting_history.append({"player_id": pid, "action": FOLD, "amount": 0, "street": self.street})
            self._advance_or_close(pid)
            return

        if action == CHECK:
            if self.to_call != 0:
                raise ValueError("Cannot check when there is a bet to call")
            self.betting_history.append({"player_id": pid, "action": CHECK, "amount": 0, "street": self.street})
            self.last_bet_size = 0.0 if self.raises_this_street == 0 else self.last_bet_size
            self._advance_or_close(pid)
            return

        if action == CALL:
            amount = min(my_stack, self.to_call)
            self._commit(pid, amount)
            self.betting_history.append({"player_id": pid, "action": CALL, "amount": amount, "street": self.street})
            self._advance_or_close(pid)
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

        prev_bet = self.street_bets[pid]
        self._commit(pid, amount)
        self.raises_this_street += 1
        self.last_bet_size = self.street_bets[pid] - prev_bet
        self.betting_history.append({"player_id": pid, "action": action, "amount": amount, "street": self.street})
        # A raise reopens the action: everyone else must act again.
        self.acted_this_street = {pid}
        self._advance_or_close(pid)
        return

    # ---- turn order / street closing ----------------------------------------

    def _next_actionable(self, from_pid: int) -> Optional[int]:
        """Next player clockwise from from_pid who can still act, or None if nobody can."""
        actionable = set(self.actionable_players())
        if not actionable:
            return None
        for offset in range(1, self.num_players + 1):
            cand = (from_pid + offset) % self.num_players
            if cand in actionable:
                return cand
        return None

    def _advance_or_close(self, just_acted_pid: int) -> None:
        live = self.live_players()
        if len(live) <= 1:
            self.terminal_flag = True
            return

        actionable = self.actionable_players()
        if len(actionable) <= 1:
            # At most one player left who could still act. If everyone's bets are
            # already equalized (or they're all-in), nobody NEEDS to act -- fast
            # forward the remaining streets straight to showdown. Otherwise the
            # lone actionable player still gets to act (e.g. call/fold to an all-in).
            max_bet = max((self.street_bets[i] for i in live), default=0.0)
            all_matched = all(
                abs(self.street_bets[i] - max_bet) < 1e-9 or i in self.all_in for i in live
            )
            if all_matched:
                self._run_out_remaining_streets()
                return
            self.current_player = actionable[0]
            self._update_to_call()
            return

        max_bet = max(self.street_bets[i] for i in live)
        street_closed = all(
            (abs(self.street_bets[i] - max_bet) < 1e-9 and i in self.acted_this_street) or i in self.all_in
            for i in actionable
        )
        if street_closed:
            self.advance_street()
        else:
            nxt = self._next_actionable(just_acted_pid)
            if nxt is None:
                self._run_out_remaining_streets()
                return
            self.current_player = nxt
            self._update_to_call()

    def advance_street(self) -> None:
        """Move to next street; reset street_bets and raises_this_street. If river done, terminal."""
        self.street += 1
        self.street_bets = [0.0] * self.num_players
        self.raises_this_street = 0
        self.last_bet_size = 0.0
        self.acted_this_street = set()
        if self.street > 3:
            self.terminal_flag = True
            return
        # First to act postflop is the first actionable player left of the button.
        nxt = self._next_actionable(self.button)
        if nxt is None:
            self._run_out_remaining_streets()
            return
        self.current_player = nxt
        self._update_to_call()

    def _run_out_remaining_streets(self) -> None:
        """Everyone left who could act is all-in (or only one non-folded player remains
        with bets already equal) -- deal through to the river with no further betting."""
        self.street += 1
        self.street_bets = [0.0] * self.num_players
        self.raises_this_street = 0
        self.last_bet_size = 0.0
        self.acted_this_street = set()
        if self.street > 3:
            self.terminal_flag = True
            return
        nxt = self._next_actionable(self.button)
        if nxt is None:
            self._run_out_remaining_streets()
            return
        self.current_player = nxt
        self._update_to_call()

    def is_terminal(self) -> bool:
        """True if hand is over (all-but-one folded, or end of river)."""
        return self.terminal_flag

    # ---- showdown / side pots ------------------------------------------------

    def resolve_showdown(self, evaluator: Any) -> List[float]:
        """
        Resolve the hand and return each player's chip delta (can be a showdown among
        >2 live players, with side pots if contributions differ due to all-ins).

        `evaluator` is a plain callable(hand1, hand2) -> int (positive if hand1 wins,
        negative if hand2 wins, 0 for a tie) -- evaluation.hand_evaluator.compare's
        own signature, so callers can pass that function directly instead of
        wrapping it in an adapter object.
        """
        live = self.live_players()
        n = self.num_players
        deltas = [0.0] * n

        if len(live) == 1:
            winner = live[0]
            deltas[winner] = self.pot
            return deltas

        if evaluator is None:
            # No evaluator available: split the pot evenly among live players.
            share = self.pot / len(live)
            for i in live:
                deltas[i] = share
            return deltas

        hands = {}
        for i in live:
            cards = self.private_cards.get(i, []) + self.board
            hands[i] = cards if len(cards) >= 5 else None

        # Build side pots from each player's total contribution (folded players'
        # chips count toward the pot layers they contributed to, but folded
        # players are never eligible to win any layer).
        contributions = {i: self.total_contributed[i] for i in range(n) if self.total_contributed[i] > 1e-9}
        if not contributions:
            share = self.pot / len(live)
            for i in live:
                deltas[i] = share
            return deltas

        levels = sorted(set(contributions.values()))
        prev_level = 0.0
        for level in levels:
            layer_span = level - prev_level
            if layer_span <= 1e-9:
                prev_level = level
                continue
            contributors_at_level = [i for i, c in contributions.items() if c >= level - 1e-9]
            layer_pot = layer_span * len(contributors_at_level)
            eligible = [i for i in contributors_at_level if i in live]
            prev_level = level

            if not eligible:
                continue  # everyone who funded this layer folded; no one to award it to (shouldn't happen)
            if len(eligible) == 1:
                deltas[eligible[0]] += layer_pot
                continue

            best = None
            winners = []
            for i in eligible:
                if hands[i] is None:
                    continue
                if best is None:
                    best = hands[i]
                    winners = [i]
                    continue
                cmp = evaluator(hands[i], best)
                if cmp > 0:
                    best = hands[i]
                    winners = [i]
                elif cmp == 0:
                    winners.append(i)
            if not winners:
                winners = eligible
            share = layer_pot / len(winners)
            for w in winners:
                deltas[w] += share

        return deltas

    def clone(self) -> "GameState":
        """Deep copy of state."""
        return copy.deepcopy(self)
