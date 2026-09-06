import unittest

from engine.game_state import GameState
from engine.action_space import get_legal_actions, CHECK, CALL, FOLD, BET_25, BET_50, BET_100, ALL_IN


class TestActionSpace(unittest.TestCase):
    def test_raise_cap_blocks_additional_raises(self):
        state = GameState(
            stacks=[50.0, 50.0],
            pot=3.0,
            street=1,
            current_player=0,
            raises_this_street=2,
            last_bet_size=1.0,
            street_bets=[1.0, 2.0],
        )
        legal = get_legal_actions(state, 0)
        self.assertIn(FOLD, legal)
        self.assertIn(CALL, legal)
        self.assertNotIn(BET_25, legal)
        self.assertNotIn(BET_50, legal)
        self.assertNotIn(BET_100, legal)
        self.assertNotIn(ALL_IN, legal)

    def test_check_not_legal_when_facing_bet(self):
        state = GameState(
            stacks=[50.0, 50.0],
            pot=3.0,
            street=1,
            current_player=0,
            raises_this_street=0,
            last_bet_size=1.0,
            street_bets=[0.0, 1.0],
        )
        legal = get_legal_actions(state, 0)
        self.assertNotIn(CHECK, legal)
        self.assertIn(CALL, legal)

    def test_short_stack_facing_a_bet_can_go_all_in_for_less(self):
        """Regression test: a player whose remaining stack is LESS than the
        amount needed to call used to get neither CALL (blocked: stack < to_call)
        nor ALL_IN (blocked: the old check required stack > to_call) -- leaving
        only FOLD, so a short-stacked player facing any bigger bet could never
        actually play the hand. ALL_IN must be offered as a capped call here."""
        state = GameState(
            stacks=[5.0, 100.0],   # player 0 has only 5 chips left
            pot=20.0,
            street=1,
            current_player=0,
            raises_this_street=0,
            last_bet_size=50.0,
            street_bets=[0.0, 50.0],  # facing a 50-chip bet, can't fully call
        )
        legal = get_legal_actions(state, 0)
        self.assertIn(FOLD, legal)
        self.assertNotIn(CALL, legal)  # can't fully call -- correctly excluded
        self.assertIn(ALL_IN, legal)   # but must still be able to shove for less

    def test_short_stack_all_in_for_less_survives_the_raise_cap(self):
        """An all-in for less is a capped call, not a raise -- it must stay legal
        even after the raise cap (2 raises/street) has already been hit, since it
        can't reopen the action the way a genuine raise would."""
        state = GameState(
            stacks=[5.0, 100.0],
            pot=20.0,
            street=1,
            current_player=0,
            raises_this_street=2,  # cap already hit
            last_bet_size=50.0,
            street_bets=[0.0, 50.0],
        )
        legal = get_legal_actions(state, 0)
        self.assertIn(FOLD, legal)
        self.assertNotIn(CALL, legal)
        self.assertIn(ALL_IN, legal)
        self.assertNotIn(BET_25, legal)
        self.assertNotIn(BET_50, legal)
        self.assertNotIn(BET_100, legal)

    def test_exact_stack_match_excludes_redundant_all_in(self):
        """When the remaining stack exactly equals the call amount, CALL alone
        covers it -- no need for a redundant identical ALL_IN option."""
        state = GameState(
            stacks=[50.0, 100.0],
            pot=20.0,
            street=1,
            current_player=0,
            raises_this_street=0,
            last_bet_size=50.0,
            street_bets=[0.0, 50.0],
        )
        legal = get_legal_actions(state, 0)
        self.assertIn(CALL, legal)
        self.assertNotIn(ALL_IN, legal)


if __name__ == "__main__":
    unittest.main()
