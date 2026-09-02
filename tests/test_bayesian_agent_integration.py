import unittest

from agents.bayesian_agent import BayesianAgent
from agents.random_agent import RandomAgent
from engine.game_engine import play_hand
from evaluation.hand_evaluator import compare as compare_hands


class _Eval:
    @staticmethod
    def compare(h1, h2):
        return compare_hands(h1, h2)


class TestBayesianAgentIntegration(unittest.TestCase):
    """
    End-to-end smoke test: play full hands through the real engine with a
    BayesianAgent, exercising act(), observe(), belief updates, the
    preflop->postflop belief transition, and entropy tracking together.
    """

    def test_plays_full_hands_and_tracks_entropy(self):
        agent = BayesianAgent(player_id=0, epsilon=0.05, samples=20, seed=7, opponent_type="TIGHT")
        opponent = RandomAgent(player_id=1, rng=None)

        for hand_seed in (101, 202, 303):
            agent.reset()
            result = play_hand(agent, opponent, seed=hand_seed, evaluator=_Eval(), return_details=True)
            self.assertIn(result["outcome"], ("fold", "showdown", "tie"))
            self.assertEqual(len(result["chip_delta"]), 2)
            # Chip deltas must be zero-sum.
            self.assertAlmostEqual(sum(result["chip_delta"]), 0.0, places=6)

        # The Bayesian agent should have recorded belief entropy at least once
        # across the hands it acted in.
        self.assertGreater(len(agent._entropy_history), 0)
        # Entropy is a valid (non-negative) information-theoretic quantity.
        self.assertTrue(all(e >= 0.0 for e in agent._entropy_history))

    def test_same_seed_is_reproducible_for_bayesian_agent(self):
        def run():
            agent = BayesianAgent(player_id=0, epsilon=0.05, samples=20, seed=7, opponent_type="TIGHT")
            opponent = RandomAgent(player_id=1, rng=__import__("random").Random(3))
            return play_hand(agent, opponent, seed=555, evaluator=_Eval(), return_details=True)["chip_delta"]

        self.assertEqual(run(), run())


if __name__ == "__main__":
    unittest.main()
