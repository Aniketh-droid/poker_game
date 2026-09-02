import math
import unittest

from belief.entropy import compute_entropy


class TestEntropy(unittest.TestCase):
    def test_uniform_distribution_has_max_entropy(self):
        dist = {"A": 0.2, "B": 0.2, "C": 0.2, "D": 0.2, "E": 0.2}
        self.assertAlmostEqual(compute_entropy(dist), math.log(5), places=6)

    def test_degenerate_distribution_has_zero_entropy(self):
        dist = {"A": 1.0, "B": 0.0, "C": 0.0}
        self.assertAlmostEqual(compute_entropy(dist), 0.0, places=6)

    def test_more_uncertain_distribution_has_higher_entropy(self):
        certain = {"A": 0.9, "B": 0.1}
        uncertain = {"A": 0.5, "B": 0.5}
        self.assertLess(compute_entropy(certain), compute_entropy(uncertain))


if __name__ == "__main__":
    unittest.main()
