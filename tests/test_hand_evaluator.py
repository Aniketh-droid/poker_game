import unittest

from evaluation.hand_evaluator import evaluate_7card, compare


class TestHandEvaluator(unittest.TestCase):
    def test_straight_flush_beats_quads(self):
        straight_flush = [(10, 1), (11, 1), (12, 1), (13, 1), (14, 1), (2, 0), (3, 2)]
        quads = [(9, 0), (9, 1), (9, 2), (9, 3), (14, 0), (4, 1), (2, 2)]
        self.assertGreater(evaluate_7card(straight_flush), evaluate_7card(quads))

    def test_pair_beats_high_card(self):
        pair = [(14, 0), (14, 1), (2, 2), (5, 0), (8, 1), (9, 2), (11, 3)]
        high = [(14, 0), (13, 1), (2, 2), (5, 0), (8, 1), (9, 2), (11, 3)]
        self.assertGreater(compare(pair, high), 0)


if __name__ == "__main__":
    unittest.main()
