import unittest

from belief.bayesian_update import update_belief


class _Ctx:
    street = 2


class TestBayesianUpdate(unittest.TestCase):
    def test_update_normalizes_distribution(self):
        prior = {
            "STRONG_MADE": 0.2,
            "MEDIUM_MADE": 0.2,
            "WEAK_MADE": 0.2,
            "STRONG_DRAW": 0.15,
            "WEAK_DRAW": 0.15,
            "AIR": 0.1,
        }
        post = update_belief(prior, "BET_100", _Ctx, opponent_type="AGGRESSIVE")
        self.assertAlmostEqual(sum(post.values()), 1.0, places=8)
        # Posterior should differ from prior after an informative action.
        max_delta = max(abs(post[k] - prior[k]) for k in prior)
        self.assertGreater(max_delta, 1e-6)


if __name__ == "__main__":
    unittest.main()
