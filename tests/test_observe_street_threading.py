import unittest

from agents.base_agent import BaseAgent
from agents.random_agent import RandomAgent
from engine.game_engine import play_hand


class _RecordingAgent(BaseAgent):
    """Wraps a RandomAgent's act(), and records every (action, street) pair
    the engine reports to observe() - used to verify the engine actually
    threads the real street through instead of silently defaulting to 0."""

    def __init__(self, player_id: int, seed: int):
        import random
        self.player_id = player_id
        self._inner = RandomAgent(player_id=player_id, rng=random.Random(seed))
        self.observed = []

    def act(self, game_state):
        return self._inner.act(game_state)

    def observe(self, opponent_action: str, street: int = 0, actor_id: int = None) -> None:
        self.observed.append((opponent_action, street))


class TestObserveStreetThreading(unittest.TestCase):
    def test_engine_reports_the_real_street_not_always_zero(self):
        """
        Regression test: engine.game_engine.play_hand used to call
        observe(action) with no street argument, so BayesianAgent-style
        agents always saw street=0 even on the flop/turn/river. Across
        enough random hands, some should reach street >= 1, and the
        recorded street for those actions must reflect that - never
        silently 0 for a postflop action.
        """
        recorder = _RecordingAgent(player_id=0, seed=1)
        villain = RandomAgent(player_id=1)

        max_street_seen = 0
        for seed in range(60):
            recorder.observed.clear()
            play_hand(recorder, villain, seed=seed)
            if recorder.observed:
                max_street_seen = max(max_street_seen, max(s for _, s in recorder.observed))

        self.assertGreater(
            max_street_seen, 0,
            "Never observed a postflop action across 60 hands - street is not being threaded through.",
        )

    def test_recorded_street_matches_the_street_the_action_was_taken_on(self):
        """
        More precise check: within a single hand, the streets reported to
        observe() must be non-decreasing (the engine reports actions in the
        order they happened, street never goes backwards).
        """
        recorder = _RecordingAgent(player_id=0, seed=2)
        villain = RandomAgent(player_id=1)

        found_multi_street_hand = False
        for seed in range(60):
            recorder.observed.clear()
            play_hand(recorder, villain, seed=seed)
            streets = [s for _, s in recorder.observed]
            self.assertEqual(streets, sorted(streets), f"streets went backwards: {streets}")
            if streets and streets[-1] > streets[0]:
                found_multi_street_hand = True

        self.assertTrue(
            found_multi_street_hand,
            "Never saw a hand where the observed street increased - can't confirm street threading works across streets.",
        )


if __name__ == "__main__":
    unittest.main()
