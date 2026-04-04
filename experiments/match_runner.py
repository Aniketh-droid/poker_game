"""
Match runner: run_match(agent1, agent2, hands=10000). Track chip delta, win rate, bluff count, entropy history.
"""

import random
from typing import List, Any, Optional, Dict

from engine.game_engine import play_hand
from engine.action_space import BET_25, BET_50, BET_100, ALL_IN
from belief.hand_bucketing import classify_preflop, classify_postflop, AIR, WEAK_DRAW, WEAK_MADE, SPECULATIVE, TRASH


def run_match(
    agent1: Any,
    agent2: Any,
    hands: int = 10000,
    seed: Optional[int] = None,
    evaluator: Any = None,
    progress_interval: int = 0,
) -> dict:
    """
    Run a match of N hands. Track chip delta, win rate, bluff count, entropy history.
    Returns dict with chip_deltas, win_rate_agent1, win_rate_agent2, bluff_count_agent1, bluff_count_agent2,
    entropy_history (if agent1 or agent2 is BayesianAgent).
    """
    if evaluator is None:
        from evaluation.hand_evaluator import compare as compare_hands
        evaluator = type("Eval", (), {"compare": staticmethod(compare_hands)})()

    rng = random.Random(seed)
    chip_deltas: List[float] = []
    wins_1 = wins_2 = ties = 0
    bluff_1 = bluff_2 = 0
    bluff_attempts_1 = bluff_attempts_2 = 0
    entropy_history: List[float] = []

    prev_entropy_1 = len(getattr(agent1, "_entropy_history", []))
    prev_entropy_2 = len(getattr(agent2, "_entropy_history", []))

    for i in range(hands):
        # Reset agents each hand since our Bayesian belief tracks current hole cards, not cross-hand opponent type.
        agent1.reset() if hasattr(agent1, "reset") else None
        agent2.reset() if hasattr(agent2, "reset") else None
        
        hand_seed = rng.randint(0, 2**31 - 1)
        hand_result = play_hand(agent1, agent2, seed=hand_seed, evaluator=evaluator, return_details=True)
        delta = hand_result["chip_delta"]
        chip_deltas.append(delta[0])
        if hand_result.get("outcome") == "tie":
            ties += 1
        elif delta[0] > 0:
            wins_1 += 1
        elif delta[0] < 0:
            wins_2 += 1
        # Only append NEW entropy samples from this hand.
        ent1 = getattr(agent1, "_entropy_history", [])
        ent2 = getattr(agent2, "_entropy_history", [])
        if len(ent1) > prev_entropy_1:
            entropy_history.extend(ent1[prev_entropy_1:])
        if len(ent2) > prev_entropy_2:
            entropy_history.extend(ent2[prev_entropy_2:])
        prev_entropy_1 = len(ent1)
        prev_entropy_2 = len(ent2)
        # Bluff metric (stronger proxy):
        # An aggressive action (bet/raise) with weak hand class, then losing the hand.
        bet_actions = {BET_25, BET_50, BET_100, ALL_IN}
        board = hand_result.get("board", [])
        cards = hand_result.get("private_cards", {})
        p0_hand = cards.get(0, [])
        p1_hand = cards.get(1, [])
        p0_bucket = classify_postflop(p0_hand, board) if len(board) >= 3 else classify_preflop(p0_hand)
        p1_bucket = classify_postflop(p1_hand, board) if len(board) >= 3 else classify_preflop(p1_hand)
        weak_buckets = {AIR, WEAK_DRAW, WEAK_MADE, SPECULATIVE, TRASH}
        p0_aggressive = any(a in bet_actions for a in hand_result.get("actions_by_player", {}).get(0, []))
        p1_aggressive = any(a in bet_actions for a in hand_result.get("actions_by_player", {}).get(1, []))
        if p0_aggressive and p0_bucket in weak_buckets:
            bluff_attempts_1 += 1
            if delta[0] < 0:
                bluff_1 += 1
        if p1_aggressive and p1_bucket in weak_buckets:
            bluff_attempts_2 += 1
            if delta[1] < 0:
                bluff_2 += 1

        if progress_interval and (i + 1) % progress_interval == 0:
            print(f"[run_match] completed {i + 1}/{hands} hands")

    total_hands = len(chip_deltas)
    return {
        "chip_deltas": chip_deltas,
        "win_rate_agent1": wins_1 / total_hands if total_hands else 0,
        "win_rate_agent2": wins_2 / total_hands if total_hands else 0,
        "tie_rate": ties / total_hands if total_hands else 0,
        "bluff_count_agent1": bluff_1,
        "bluff_count_agent2": bluff_2,
        "bluff_attempts_agent1": bluff_attempts_1,
        "bluff_attempts_agent2": bluff_attempts_2,
        "bluff_failure_rate_agent1": (bluff_1 / bluff_attempts_1) if bluff_attempts_1 else 0.0,
        "bluff_failure_rate_agent2": (bluff_2 / bluff_attempts_2) if bluff_attempts_2 else 0.0,
        "entropy_history": entropy_history,
        "total_hands": total_hands,
    }
