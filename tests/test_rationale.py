import unittest
from types import SimpleNamespace

from decision.rationale import explain_decision
from engine.action_space import FOLD, CHECK, CALL, BET_50


def _agent(cls_name, **attrs):
    """A minimal stand-in with the given class name (explain_decision
    branches on type(agent_obj).__name__) and whatever decision-time
    attributes that branch reads."""
    return type(cls_name, (), attrs)()


class TestHandAndContextInSummary(unittest.TestCase):
    """
    explain_decision should ground its explanation in the agent's real hole
    cards, the real board, and the real actions already taken this street --
    not just an abstract strategy description.
    """

    def _state(self, hole, board, street=1):
        return SimpleNamespace(private_cards={1: hole}, board=board, street=street)

    def test_names_actual_hole_cards_and_board(self):
        agent = _agent("CallingStationAgent", _last_bucket="WEAK_DRAW")
        state = self._state(hole=[(9, 2), (4, 1)], board=[(13, 2), (7, 1), (2, 3), (12, 0)])
        entry = explain_decision(agent, CHECK, [CHECK, BET_50], seat_idx=1, game_state=state)
        self.assertIn("9♠ 4♦", entry["summary"])
        self.assertIn("K♠ 7♦ 2♣ Q♥", entry["summary"])

    def test_preflop_has_no_board_clause(self):
        agent = _agent("TightAgent", _last_bucket="PREMIUM")
        state = self._state(hole=[(14, 0), (14, 1)], board=[], street=0)
        entry = explain_decision(agent, BET_50, [BET_50, FOLD], seat_idx=1, game_state=state)
        self.assertIn("preflop", entry["summary"])
        self.assertNotIn("board of", entry["summary"])

    def test_narrates_prior_actions_on_same_street_only(self):
        agent = _agent("CallingStationAgent", _last_bucket="AIR")
        state = self._state(hole=[(9, 2), (4, 1)], board=[(13, 2), (7, 1), (2, 3)], street=1)
        prior = [
            {"seat": 0, "name": "The Mathematician", "action": CHECK, "street": 1},
            {"seat": 3, "name": "The Maniac", "action": BET_50, "street": 1},
            {"seat": 2, "name": "The Rock", "action": FOLD, "street": 0},  # different street -- excluded
        ]
        entry = explain_decision(agent, CALL, [FOLD, CALL], seat_idx=1, game_state=state, prior_actions=prior)
        self.assertIn("After The Mathematician checked and The Maniac bet half the pot", entry["summary"])
        self.assertNotIn("The Rock", entry["summary"])

    def test_no_game_state_falls_back_gracefully(self):
        agent = _agent("RandomAgent")
        entry = explain_decision(agent, FOLD, [FOLD, CHECK], seat_idx=1)
        self.assertTrue(entry["summary"])

    def test_data_scientist_reports_its_actual_blend_weight(self):
        agent = _agent("DataScientistAgent", _last_ev_dict={"CALL": 1.0, "FOLD": 0.0}, _last_bayes_weight=0.62)
        entry = explain_decision(agent, CALL, [CALL, FOLD], seat_idx=1)
        self.assertIn("62%", entry["summary"])
        self.assertIn("38%", entry["summary"])


if __name__ == "__main__":
    unittest.main()
