import unittest

from belief.hand_bucketing import (
    classify_preflop,
    classify_postflop,
    PREMIUM,
    TRASH,
    STRONG_MADE,
    AIR,
)


class TestHandBucketingPreflop(unittest.TestCase):
    def test_pocket_aces_is_premium(self):
        self.assertEqual(classify_preflop([(14, 0), (14, 1)]), PREMIUM)

    def test_seven_deuce_offsuit_is_trash(self):
        self.assertEqual(classify_preflop([(7, 0), (2, 1)]), TRASH)

    def test_ak_is_premium_regardless_of_suitedness(self):
        self.assertEqual(classify_preflop([(14, 0), (13, 0)]), PREMIUM)  # suited
        self.assertEqual(classify_preflop([(14, 0), (13, 1)]), PREMIUM)  # offsuit


class TestHandBucketingPostflop(unittest.TestCase):
    def test_quads_is_strong_made(self):
        hand = [(9, 0), (9, 1)]
        board = [(9, 2), (9, 3), (2, 0)]
        self.assertEqual(classify_postflop(hand, board), STRONG_MADE)

    def test_disconnected_no_draw_hand_is_air(self):
        # Hero holds 7-2 (suit 1), board is three suit-2 cards far away in rank
        # (no pair, no flush draw for hero's suit, no straight-ish gap <= 2).
        hand = [(2, 0), (7, 1)]
        board = [(13, 2), (12, 2), (11, 2)]
        self.assertEqual(classify_postflop(hand, board), AIR)

    def test_postflop_falls_back_to_preflop_before_flop(self):
        hand = [(14, 0), (14, 1)]
        self.assertEqual(classify_postflop(hand, []), classify_preflop(hand))


if __name__ == "__main__":
    unittest.main()
