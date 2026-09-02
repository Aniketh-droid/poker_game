import unittest
from types import SimpleNamespace

from belief.opponent_model import (
    get_fold_probability,
    get_call_probability,
    likelihood_action_given_bucket,
    TIGHT,
    LOOSE,
)
from engine.action_space import FOLD


class TestOpponentModel(unittest.TestCase):
    def test_fold_probability_matches_bucket_table_at_street_zero(self):
        gs = SimpleNamespace(street=0)
        # PREMIUM never folds preflop; TRASH folds heavily.
        self.assertAlmostEqual(get_fold_probability({"PREMIUM": 1.0}, gs), 0.00)
        self.assertAlmostEqual(get_fold_probability({"TRASH": 1.0}, gs), 0.80)

    def test_call_probability_matches_bucket_table_at_street_zero(self):
        gs = SimpleNamespace(street=0)
        self.assertAlmostEqual(get_call_probability({"PREMIUM": 1.0}, gs), 1.00)
        self.assertAlmostEqual(get_call_probability({"TRASH": 1.0}, gs), 0.08)

    def test_belief_weighted_average(self):
        # A 50/50 belief between PREMIUM (never folds) and TRASH (folds 80%)
        # should average to 40% fold probability preflop.
        gs = SimpleNamespace(street=0)
        belief = {"PREMIUM": 0.5, "TRASH": 0.5}
        self.assertAlmostEqual(get_fold_probability(belief, gs), 0.40)

    def test_tight_opponent_folds_more_than_loose_for_same_bucket(self):
        # TIGHT scales fold probability up (1.30x), LOOSE scales it down (0.80x).
        tight_fold = likelihood_action_given_bucket(FOLD, "MEDIUM", street=0, opponent_type=TIGHT)
        loose_fold = likelihood_action_given_bucket(FOLD, "MEDIUM", street=0, opponent_type=LOOSE)
        self.assertGreater(tight_fold, loose_fold)


if __name__ == "__main__":
    unittest.main()
