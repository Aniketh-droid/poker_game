import random
import unittest

from evaluation.monte_carlo import estimate_equity


class TestMonteCarloEquity(unittest.TestCase):
    def test_probabilities_are_in_valid_range(self):
        win, tie = estimate_equity(
            hero_cards=[(14, 0), (14, 1)],
            board=[],
            samples=200,
            rng=random.Random(1),
        )
        self.assertGreaterEqual(win, 0.0)
        self.assertLessEqual(win + tie, 1.0)

    def test_pocket_aces_has_strong_preflop_equity(self):
        # Heads-up, AA vs a uniformly random hand wins roughly 85% of the time.
        # 300 samples gives a comfortable margin above 0.65 for a stable, non-flaky assertion.
        win, tie = estimate_equity(
            hero_cards=[(14, 0), (14, 1)],
            board=[],
            samples=300,
            rng=random.Random(42),
        )
        self.assertGreater(win + 0.5 * tie, 0.65)

    def test_same_seed_gives_reproducible_equity(self):
        kwargs = dict(hero_cards=[(14, 0), (13, 0)], board=[(2, 1), (7, 2), (9, 3)], samples=100)
        result_a = estimate_equity(rng=random.Random(99), **kwargs)
        result_b = estimate_equity(rng=random.Random(99), **kwargs)
        self.assertEqual(result_a, result_b)


if __name__ == "__main__":
    unittest.main()
