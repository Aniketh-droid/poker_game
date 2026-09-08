import unittest

from agents.bayesian_agent import BayesianAgent
from agents.random_agent import RandomAgent
from engine.game_engine import play_hand
from engine.action_space import FOLD, CALL, BET_50


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
            result = play_hand(agent, opponent, seed=hand_seed, return_details=True)
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
            return play_hand(agent, opponent, seed=555, return_details=True)["chip_delta"]

        self.assertEqual(run(), run())


class TestAdaptiveOpponentType(unittest.TestCase):
    """
    _effective_opponent_type should stick to the static archetype guess until
    enough hands are observed, then classify from real behavior instead.
    """

    def test_falls_back_to_static_type_below_the_observation_floor(self):
        agent = BayesianAgent(player_id=0, seed=1, opponent_type="LOOSE")
        for _ in range(agent._ADAPT_MIN_HANDS - 1):
            agent.observe(FOLD, street=0, actor_id=1)  # would read as TIGHT if trusted early
        self.assertEqual(agent._effective_opponent_type(1), "LOOSE")

    def test_switches_to_tight_once_a_high_fold_rate_is_established(self):
        agent = BayesianAgent(player_id=0, seed=1, opponent_type="LOOSE")
        for _ in range(agent._ADAPT_MIN_HANDS + 5):
            agent.observe(FOLD, street=0, actor_id=1)
        self.assertEqual(agent._effective_opponent_type(1), "TIGHT")

    def test_switches_to_aggressive_once_a_high_bet_rate_is_established(self):
        agent = BayesianAgent(player_id=0, seed=1, opponent_type="TIGHT")
        for _ in range(agent._ADAPT_MIN_HANDS + 5):
            agent.observe(BET_50, street=0, actor_id=1)
        self.assertEqual(agent._effective_opponent_type(1), "AGGRESSIVE")

    def test_stays_loose_for_a_mostly_calling_opponent(self):
        agent = BayesianAgent(player_id=0, seed=1, opponent_type="TIGHT")
        for _ in range(agent._ADAPT_MIN_HANDS + 5):
            agent.observe(CALL, street=0, actor_id=1)
        self.assertEqual(agent._effective_opponent_type(1), "LOOSE")

    def test_different_opponents_are_classified_independently(self):
        agent = BayesianAgent(player_id=0, seed=1, opponent_type="LOOSE")
        for _ in range(agent._ADAPT_MIN_HANDS + 5):
            agent.observe(FOLD, street=0, actor_id=1)
            agent.observe(BET_50, street=0, actor_id=2)
        self.assertEqual(agent._effective_opponent_type(1), "TIGHT")
        self.assertEqual(agent._effective_opponent_type(2), "AGGRESSIVE")


if __name__ == "__main__":
    unittest.main()
