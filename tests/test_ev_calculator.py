import unittest
from types import SimpleNamespace

from decision.ev_calculator import compute_ev
from engine.action_space import FOLD, CHECK, CALL
from engine.game_state import GameState


def _make_state(pot, street_bets, hero_cards, board=None, stacks=None):
    """
    Build a minimal stand-in for GameState with just the attributes
    compute_ev reads, plus a pre-seeded equity cache so no Monte Carlo
    sampling is needed for these arithmetic tests.
    """
    board = board or []
    stacks = stacks or [50.0, 50.0]
    state = SimpleNamespace(
        pot=pot,
        stacks=stacks,
        street_bets=street_bets,
        private_cards={0: hero_cards, 1: []},
        board=board,
    )
    return state


def _seed_equity_cache(state, hero_cards, board, samples, win_prob, tie_prob, hero_id=0, belief=None):
    """Pre-populate compute_ev's internal equity cache so it skips real sampling."""
    from decision.ev_calculator import _belief_cache_key

    key = (hero_id, tuple(hero_cards), tuple(board), _belief_cache_key(belief), samples)
    state._equity_cache = {key: (win_prob, tie_prob)}


class TestEvCalculator(unittest.TestCase):
    def test_fold_ev_is_always_zero(self):
        state = _make_state(pot=10.0, street_bets=[2.0, 4.0], hero_cards=[(14, 0), (14, 1)])
        self.assertEqual(compute_ev(FOLD, state, hero_id=0), 0.0)

    def test_check_ev_uses_equity_times_pot_with_no_cost(self):
        hero_cards = [(14, 0), (14, 1)]
        state = _make_state(pot=10.0, street_bets=[0.0, 0.0], hero_cards=hero_cards)
        _seed_equity_cache(state, hero_cards, [], samples=5, win_prob=0.6, tie_prob=0.2)
        ev = compute_ev(CHECK, state, hero_id=0, samples=5)
        equity = 0.6 + 0.2 * 0.5  # 0.7
        self.assertAlmostEqual(ev, equity * 10.0 - 0.0)

    def test_call_ev_only_subtracts_this_streets_cost(self):
        hero_cards = [(14, 0), (14, 1)]
        state = _make_state(pot=10.0, street_bets=[2.0, 4.0], hero_cards=hero_cards)
        _seed_equity_cache(state, hero_cards, [], samples=5, win_prob=0.6, tie_prob=0.2)
        ev = compute_ev(CALL, state, hero_id=0, samples=5)
        equity = 0.7
        cost = 2.0  # to_call = 4.0 - 2.0
        final_pot = 10.0 + cost
        self.assertAlmostEqual(ev, equity * final_pot - cost)

    def test_call_ev_does_not_depend_on_prior_sunk_investment(self):
        """
        Regression test for the sunk-cost bug: two states with identical
        pot and identical to_call, but very different amounts already
        invested this street (2 vs 20), must produce the same CALL EV.
        The old buggy formula subtracted amount_invested as well as cost,
        which would have made the heavier-invested state's EV much lower.
        """
        hero_cards = [(14, 0), (14, 1)]

        state_a = _make_state(pot=10.0, street_bets=[2.0, 4.0], hero_cards=hero_cards)
        _seed_equity_cache(state_a, hero_cards, [], samples=5, win_prob=0.6, tie_prob=0.2)

        state_b = _make_state(pot=10.0, street_bets=[20.0, 22.0], hero_cards=hero_cards)
        _seed_equity_cache(state_b, hero_cards, [], samples=5, win_prob=0.6, tie_prob=0.2)

        ev_a = compute_ev(CALL, state_a, hero_id=0, samples=5)
        ev_b = compute_ev(CALL, state_b, hero_id=0, samples=5)
        self.assertAlmostEqual(ev_a, ev_b)


    def test_call_ev_finds_the_real_opponent_at_a_multiway_table_reduced_to_heads_up(self):
        """
        Regression test for the `street_bets[1 - pid]` hardcoded-heads-up bug:
        compute_ev() is called by EVAgent/BayesianAgent whenever exactly one
        opponent is still live, even at a 6-max table. If the two live seats
        aren't 0 and 1 (e.g. seats 2 and 4, everyone else folded), `1 - pid`
        wraps around to a completely different -- and often folded, stale --
        seat's bet via negative indexing, instead of the real opponent's.
        """
        n = 6
        stacks = [50.0] * n
        street_bets = [0.0] * n
        street_bets[2] = 3.0   # hero (seat 2) already has 3 in on this street
        street_bets[4] = 9.0   # the real live opponent (seat 4) bet to 9
        folded = {0, 1, 3, 5}  # everyone else is out -- only seats 2 and 4 are live

        state = GameState(
            stacks=stacks, pot=15.0, street=1, board=[],
            private_cards={2: [(14, 0), (14, 1)], 4: []},
            current_player=2, street_bets=street_bets, folded=folded,
        )
        from decision.ev_calculator import _belief_cache_key
        key = (2, tuple(state.private_cards[2]), tuple(state.board), _belief_cache_key(None), 5)
        state._equity_cache = {key: (0.6, 0.2)}

        ev = compute_ev(CALL, state, hero_id=2, samples=5)
        # Correct to_call = 9.0 - 3.0 = 6.0 (against seat 4, the real opponent).
        # The old `street_bets[1 - 2]` == `street_bets[-1]` == seat 5's bet (0.0,
        # folded) would have produced to_call = 0.0 and a very different EV.
        equity = 0.6 + 0.2 * 0.5
        cost = 6.0
        final_pot = 15.0 + cost
        self.assertAlmostEqual(ev, equity * final_pot - cost)


if __name__ == "__main__":
    unittest.main()
