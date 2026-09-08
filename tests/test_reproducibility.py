import unittest
import random

from agents.random_agent import RandomAgent
from engine.game_engine import play_hand


class TestReproducibility(unittest.TestCase):
    def test_same_seed_same_delta(self):
        a1 = RandomAgent(player_id=0, rng=random.Random(7))
        a2 = RandomAgent(player_id=1, rng=random.Random(11))
        d1 = play_hand(a1, a2, seed=1234)

        b1 = RandomAgent(player_id=0, rng=random.Random(7))
        b2 = RandomAgent(player_id=1, rng=random.Random(11))
        d2 = play_hand(b1, b2, seed=1234)
        self.assertEqual(d1, d2)


if __name__ == "__main__":
    unittest.main()
