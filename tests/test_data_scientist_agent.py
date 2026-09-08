import unittest
from types import SimpleNamespace

from agents.data_scientist_agent import DataScientistAgent, _BAYES_WEIGHT_FLOOR, _BAYES_WEIGHT_CEILING
from belief.opponent_stats import OpponentStats
from engine.action_space import FOLD


class TestBayesConfidence(unittest.TestCase):
    """
    The ensemble blend weight should stay at the floor with no real signal on
    the live opponents, and rise toward the ceiling once the Bayesian
    sub-model has actually observed them -- reusing its own OpponentStats
    rather than tracking confidence separately.
    """

    def test_floor_with_no_opponent_data(self):
        agent = DataScientistAgent(player_id=0, seed=1)
        state = SimpleNamespace(live_players=lambda: [0, 1])
        self.assertEqual(agent._bayes_confidence(state), _BAYES_WEIGHT_FLOOR)

    def test_rises_to_ceiling_with_enough_observations(self):
        agent = DataScientistAgent(player_id=0, seed=1)
        stats = OpponentStats()
        for _ in range(agent._bayes_model._ADAPT_MIN_HANDS * 2):
            stats.record(FOLD, street=0)
        agent._bayes_model._opponent_stats[1] = stats
        state = SimpleNamespace(live_players=lambda: [0, 1])
        self.assertEqual(agent._bayes_confidence(state), _BAYES_WEIGHT_CEILING)

    def test_ignores_stats_for_seats_not_live_this_hand(self):
        agent = DataScientistAgent(player_id=0, seed=1)
        stats = OpponentStats()
        for _ in range(agent._bayes_model._ADAPT_MIN_HANDS * 2):
            stats.record(FOLD, street=0)
        agent._bayes_model._opponent_stats[2] = stats  # seat 2 folded this hand
        state = SimpleNamespace(live_players=lambda: [0, 1])
        self.assertEqual(agent._bayes_confidence(state), _BAYES_WEIGHT_FLOOR)


if __name__ == "__main__":
    unittest.main()
