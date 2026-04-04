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


if __name__ == "__main__":
    unittest.main()
