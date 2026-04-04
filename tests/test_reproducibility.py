import unittest
import random

from agents.random_agent import RandomAgent
from engine.game_engine import play_hand
from evaluation.hand_evaluator import compare as compare_hands


class _Eval:
    @staticmethod
    def compare(h1, h2):
        return compare_hands(h1, h2)


class TestReproducibility(unittest.TestCase):
    def test_same_seed_same_delta(self):
        a1 = RandomAgent(player_id=0, rng=random.Random(7))
        a2 = RandomAgent(player_id=1, rng=random.Random(11))
        d1 = play_hand(a1, a2, seed=1234, evaluator=_Eval())

        b1 = RandomAgent(player_id=0, rng=random.Random(7))
        b2 = RandomAgent(player_id=1, rng=random.Random(11))
        d2 = play_hand(b1, b2, seed=1234, evaluator=_Eval())
        self.assertEqual(d1, d2)


if __name__ == "__main__":
    unittest.main()
