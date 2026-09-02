import unittest

from belief.opponent_stats import OpponentStats, blend_with_prior
from engine.action_space import FOLD, CHECK, CALL, BET_50
from decision.ev_calculator import compute_ev
from types import SimpleNamespace


class TestOpponentStats(unittest.TestCase):
    def test_empirical_rates_none_before_any_observation(self):
        stats = OpponentStats()
        self.assertIsNone(stats.empirical_rates(0))

    def test_empirical_rates_match_recorded_frequency(self):
        stats = OpponentStats()
        # Street 1 (flop): 3 folds, 1 call, 1 bet, out of 5 total responses.
        for _ in range(3):
            stats.record(FOLD, street=1)
        stats.record(CALL, street=1)
        stats.record(BET_50, street=1)

        fold_rate, call_rate, n = stats.empirical_rates(1)
        self.assertEqual(n, 5)
        self.assertAlmostEqual(fold_rate, 3 / 5)
        self.assertAlmostEqual(call_rate, 1 / 5)

    def test_streets_are_tracked_independently(self):
        stats = OpponentStats()
        stats.record(FOLD, street=0)
        stats.record(CALL, street=2)
        self.assertEqual(stats.empirical_rates(0)[2], 1)
        self.assertEqual(stats.empirical_rates(1), None)
        self.assertEqual(stats.empirical_rates(2)[2], 1)

    def test_street_argument_is_clamped_into_range(self):
        stats = OpponentStats()
        stats.record(FOLD, street=99)  # should clamp to last street (river=3)
        self.assertEqual(stats.empirical_rates(3)[2], 1)


class TestBlendWithPrior(unittest.TestCase):
    def test_no_observations_returns_prior_unchanged(self):
        fold_prob, call_prob = blend_with_prior(0.3, 0.6, empirical=None)
        self.assertEqual((fold_prob, call_prob), (0.3, 0.6))

    def test_few_observations_stay_close_to_prior(self):
        # 1 observation vs a default prior_weight of 10 pseudo-observations:
        # the prior should still dominate.
        fold_prob, _ = blend_with_prior(0.3, 0.6, empirical=(1.0, 0.0, 1))
        self.assertLess(fold_prob, 0.4)  # nudged up from 0.3, but not much

    def test_many_observations_converge_to_empirical_rate(self):
        # 10,000 observations should swamp a prior_weight of 10.
        fold_prob, call_prob = blend_with_prior(0.3, 0.6, empirical=(0.9, 0.1, 10_000))
        self.assertAlmostEqual(fold_prob, 0.9, places=2)
        self.assertAlmostEqual(call_prob, 0.1, places=2)


class TestComputeEvUsesOpponentStats(unittest.TestCase):
    """
    Regression + behavior test: an opponent that (per the static TIGHT
    archetype prior) is assumed to fold often, but has actually never
    folded to a bet in this match, should be modeled by compute_ev as
    calling almost always once enough hands have been observed -- raising
    a bet's EV toward its "opponent calls" branch instead of its
    "opponent folds" branch.
    """

    def _make_state(self, pot, street_bets, hero_cards, board=None, stacks=None, street=1):
        board = board or []
        stacks = stacks or [50.0, 50.0]
        state = SimpleNamespace(
            pot=pot, stacks=stacks, street_bets=street_bets,
            private_cards={0: hero_cards, 1: []}, board=board, street=street,
        )
        return state

    def _seed_equity_cache(self, state, hero_cards, board, samples, win_prob, tie_prob, belief, hero_id=0):
        from decision.ev_calculator import _belief_cache_key
        key = (hero_id, tuple(hero_cards), tuple(board), _belief_cache_key(belief), samples)
        state._equity_cache = {key: (win_prob, tie_prob)}

    def test_never_folding_opponent_shifts_bet_ev_toward_call_branch(self):
        hero_cards = [(14, 0), (14, 1)]
        belief = {"AIR": 1.0}  # arbitrary non-empty belief so opponent_model path runs

        # Baseline: no opponent_stats at all (old behavior) -> uses static prior only.
        state_baseline = self._make_state(pot=10.0, street_bets=[0.0, 0.0], hero_cards=hero_cards)
        self._seed_equity_cache(state_baseline, hero_cards, [], samples=5, win_prob=0.5, tie_prob=0.0, belief=belief)
        ev_baseline = compute_ev(
            BET_50, state_baseline, belief=belief, hero_id=0, samples=5, opponent_stats=None,
        )

        # Same situation, but this opponent has responded to 200 bets on this
        # street and folded 0 of them (a pure equity-caller, like EVAgent).
        stats = OpponentStats()
        for _ in range(200):
            stats.record(CALL, street=1)

        state_adapted = self._make_state(pot=10.0, street_bets=[0.0, 0.0], hero_cards=hero_cards)
        self._seed_equity_cache(state_adapted, hero_cards, [], samples=5, win_prob=0.5, tie_prob=0.0, belief=belief)
        ev_adapted = compute_ev(
            BET_50, state_adapted, belief=belief, hero_id=0, samples=5, opponent_stats=stats,
        )

        # With equity=0.5 (a coinflip), the call-branch EV of a bet is below
        # the fold-branch EV (winning the whole pot outright). An opponent
        # correctly modeled as "always calls" should therefore have a LOWER
        # bet EV here than one modeled by the static (fold-happy AIR) prior.
        self.assertLess(ev_adapted, ev_baseline)


if __name__ == "__main__":
    unittest.main()
