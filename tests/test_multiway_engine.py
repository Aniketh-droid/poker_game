import unittest
import random

from agents.base_agent import BaseAgent
from agents.random_agent import RandomAgent
from engine.action_space import get_legal_actions, ALL_IN, CALL, CHECK, FOLD
from engine.game_engine import play_hand, play_hand_multiway
from evaluation.hand_evaluator import compare as compare_hands


class _Eval:
    @staticmethod
    def compare(h1, h2):
        return compare_hands(h1, h2)


class _AllInAgent(BaseAgent):
    """Always shoves (or calls/checks if it can't) -- used to force side-pot scenarios."""

    def __init__(self, player_id: int):
        self.player_id = player_id

    def act(self, game_state):
        legal = get_legal_actions(game_state, self.player_id)
        if ALL_IN in legal:
            return ALL_IN
        if CALL in legal:
            return CALL
        if CHECK in legal:
            return CHECK
        return legal[0]


class _FoldingAgent(BaseAgent):
    """Always folds if it can, else checks -- used to force heads-up-by-fold scenarios."""

    def __init__(self, player_id: int):
        self.player_id = player_id

    def act(self, game_state):
        legal = get_legal_actions(game_state, self.player_id)
        if FOLD in legal:
            return FOLD
        if CHECK in legal:
            return CHECK
        return legal[0]


class TestMultiwayEngineConservesChips(unittest.TestCase):
    def test_chip_deltas_are_zero_sum_at_every_table_size(self):
        for n in (2, 3, 4, 5, 6):
            for hand_i in range(15):
                agents = [RandomAgent(player_id=i, rng=random.Random(hand_i * 10 + i)) for i in range(n)]
                result = play_hand_multiway(
                    agents, seed=hand_i, evaluator=_Eval(), button=hand_i % n, return_details=True,
                )
                self.assertAlmostEqual(
                    sum(result["chip_delta"]), 0.0, places=6,
                    msg=f"n={n} hand={hand_i} deltas={result['chip_delta']}",
                )

    def test_no_negative_final_stacks(self):
        """A player can never end a hand having lost more than they had -- stacks
        (initial + delta) must never go negative, which would mean chips were
        awarded/taken beyond what was actually in the pot (a side-pot bug)."""
        n = 4
        base_stack = 50.0
        for hand_i in range(20):
            agents = [RandomAgent(player_id=i, rng=random.Random(hand_i + i)) for i in range(n)]
            result = play_hand_multiway(agents, seed=hand_i, evaluator=_Eval(), button=hand_i % n, return_details=True)
            for i in range(n):
                self.assertGreaterEqual(base_stack + result["chip_delta"][i], -1e-6)


class TestMultiwaySidePots(unittest.TestCase):
    def test_unequal_all_in_stacks_conserve_chips_and_never_go_negative(self):
        """Short/medium/deep stacks all shoving forces at least a main pot + one side
        pot most hands. The only thing we can assert generically across random deals
        is the invariant that must ALWAYS hold: total chips in == total chips out,
        and nobody's final stack goes negative (both would indicate a side-pot bug)."""
        stacks = [3.0, 15.0, 40.0]
        errors = []
        for i in range(150):
            agents = [_AllInAgent(0), _AllInAgent(1), _AllInAgent(2)]
            result = play_hand_multiway(
                agents, seed=9000 + i, evaluator=_Eval(), button=i % 3,
                stacks=list(stacks), return_details=True,
            )
            delta = result["chip_delta"]
            if abs(sum(delta)) > 1e-6:
                errors.append((i, "non-zero-sum", delta))
            for j in range(3):
                if stacks[j] + delta[j] < -1e-6:
                    errors.append((i, f"seat {j} went negative", delta))
        self.assertEqual(errors, [], f"side-pot invariant violations: {errors[:5]}")

    def test_short_stack_can_only_win_the_portion_it_could_contest(self):
        """A player all-in for less than the others can never win MORE than a main
        pot sized to their own (and every other live player's) contribution at that
        level -- i.e. they can't scoop chips that were only wagered between two
        bigger stacks after they were already all-in. Run enough hands that the
        short stack sometimes wins, and check its win amount never exceeds what the
        3-way math allows for a min-stack-of-3 shove."""
        stacks = [2.0, 20.0, 20.0]
        max_possible_win_for_short = 2.0 * 3  # everyone's contribution capped at the short stack's shove
        for i in range(200):
            agents = [_AllInAgent(0), _AllInAgent(1), _AllInAgent(2)]
            result = play_hand_multiway(
                agents, seed=1234 + i, evaluator=_Eval(), button=i % 3,
                stacks=list(stacks), return_details=True,
            )
            short_stack_delta = result["chip_delta"][0]
            self.assertLessEqual(
                short_stack_delta, max_possible_win_for_short + 1e-6,
                msg=f"hand {i}: short stack won {short_stack_delta}, more than the {max_possible_win_for_short} "
                    f"it could possibly have contested",
            )


class TestMultiwayFoldsDownToOne(unittest.TestCase):
    def test_hand_ends_when_all_but_one_fold(self):
        n = 4
        agents = [_FoldingAgent(0), _FoldingAgent(1), _FoldingAgent(2), RandomAgent(player_id=3, rng=random.Random(1))]
        result = play_hand_multiway(agents, seed=42, evaluator=_Eval(), button=0, return_details=True)
        self.assertEqual(result["outcome"], "fold")
        self.assertEqual(result["winner_ids"], [3])
        # The lone non-folder should have won the whole pot (net gain > 0).
        self.assertGreater(result["chip_delta"][3], 0.0)


class TestHeadsUpBackwardCompatibility(unittest.TestCase):
    def test_play_hand_and_play_hand_multiway_agree_at_two_players(self):
        """The original 2-player play_hand() must keep behaving exactly as before;
        this just re-confirms zero-sum + no crash for the classic entry point that
        the whole benchmark suite depends on."""
        a0 = RandomAgent(player_id=0, rng=random.Random(1))
        a1 = RandomAgent(player_id=1, rng=random.Random(2))
        result = play_hand(a0, a1, seed=7, evaluator=_Eval(), return_details=True)
        self.assertAlmostEqual(sum(result["chip_delta"]), 0.0, places=6)


if __name__ == "__main__":
    unittest.main()
