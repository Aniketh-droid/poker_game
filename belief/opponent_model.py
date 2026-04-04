"""
Opponent model: P(action | bucket, opponent_type, street). Hardcoded probability tables.

KEY FIX: Likelihood tables have been sharpened so strong hands and weak hands produce
clearly different probabilities. Previously the ratios were too similar (e.g. 2x postflop),
making Bayes unable to update meaningfully. Now strong buckets are ~5-10x more likely
to bet/raise than AIR, giving the posterior room to move.
"""

from typing import Any, Dict

from engine.action_space import FOLD, CHECK, CALL, BET_25, BET_50, BET_100, ALL_IN

# Opponent types
TIGHT = "TIGHT"
LOOSE = "LOOSE"
AGGRESSIVE = "AGGRESSIVE"

_PREFLOP_BUCKETS = ("PREMIUM", "STRONG", "MEDIUM", "SPECULATIVE", "TRASH")
_POSTFLOP_BUCKETS = ("STRONG_MADE", "MEDIUM_MADE", "WEAK_MADE", "STRONG_DRAW", "WEAK_DRAW", "AIR")

# --- FOLD probabilities P(fold | bucket, street) ---
# More extreme: PREMIUM never folds, AIR almost always folds to a bet
_FOLD_PROB = {
    "PREMIUM":      [0.00, 0.00, 0.00, 0.00],
    "STRONG":       [0.02, 0.03, 0.03, 0.03],
    "MEDIUM":       [0.15, 0.20, 0.18, 0.15],
    "SPECULATIVE":  [0.45, 0.50, 0.45, 0.40],
    "TRASH":        [0.80, 0.85, 0.88, 0.90],
    # Postflop
    "STRONG_MADE":  [0.00, 0.00, 0.00, 0.00],
    "MEDIUM_MADE":  [0.00, 0.05, 0.08, 0.10],
    "WEAK_MADE":    [0.00, 0.25, 0.30, 0.35],
    "STRONG_DRAW":  [0.00, 0.10, 0.15, 0.20],
    "WEAK_DRAW":    [0.00, 0.45, 0.55, 0.65],
    "AIR":          [0.00, 0.75, 0.82, 0.88],
}

# --- CALL probabilities P(call/check | bucket, street) ---
_CALL_PROB = {
    "PREMIUM":      [1.00, 1.00, 1.00, 1.00],
    "STRONG":       [0.95, 0.92, 0.90, 0.88],
    "MEDIUM":       [0.70, 0.65, 0.65, 0.62],
    "SPECULATIVE":  [0.40, 0.35, 0.38, 0.40],
    "TRASH":        [0.08, 0.10, 0.10, 0.08],
    # Postflop
    "STRONG_MADE":  [1.00, 1.00, 1.00, 1.00],
    "MEDIUM_MADE":  [1.00, 0.88, 0.85, 0.80],
    "WEAK_MADE":    [1.00, 0.65, 0.58, 0.52],
    "STRONG_DRAW":  [1.00, 0.78, 0.70, 0.60],
    "WEAK_DRAW":    [1.00, 0.45, 0.38, 0.28],
    "AIR":          [1.00, 0.18, 0.13, 0.09],
}

# --- BET_25 probabilities ---
# STRONG buckets bet more often; AIR/TRASH seldom bet at 25% (bluffs are rare and small)
_BET_25_PROB = {
    "PREMIUM":      [0.20, 0.18, 0.15, 0.12],
    "STRONG":       [0.30, 0.28, 0.25, 0.20],
    "MEDIUM":       [0.22, 0.25, 0.22, 0.18],
    "SPECULATIVE":  [0.18, 0.20, 0.18, 0.15],
    "TRASH":        [0.05, 0.08, 0.06, 0.04],
    # Postflop — STRONG_MADE bets frequently for value; AIR bluffs occasionally small
    "STRONG_MADE":  [0.20, 0.22, 0.18, 0.15],
    "MEDIUM_MADE":  [0.18, 0.20, 0.17, 0.14],
    "WEAK_MADE":    [0.10, 0.14, 0.12, 0.10],
    "STRONG_DRAW":  [0.18, 0.22, 0.20, 0.16],
    "WEAK_DRAW":    [0.10, 0.14, 0.12, 0.08],
    "AIR":          [0.02, 0.06, 0.04, 0.03],  # Much lower than before
}

# --- BET_50 probabilities ---
_BET_50_PROB = {
    "PREMIUM":      [0.30, 0.30, 0.28, 0.25],  # Premium loves half-pot value bets
    "STRONG":       [0.28, 0.25, 0.22, 0.18],
    "MEDIUM":       [0.18, 0.18, 0.16, 0.13],
    "SPECULATIVE":  [0.12, 0.15, 0.14, 0.12],
    "TRASH":        [0.03, 0.05, 0.04, 0.03],
    # Postflop
    "STRONG_MADE":  [0.28, 0.28, 0.25, 0.22],
    "MEDIUM_MADE":  [0.18, 0.20, 0.18, 0.15],
    "WEAK_MADE":    [0.08, 0.12, 0.11, 0.09],
    "STRONG_DRAW":  [0.18, 0.22, 0.20, 0.16],
    "WEAK_DRAW":    [0.06, 0.10, 0.09, 0.07],
    "AIR":          [0.02, 0.04, 0.03, 0.02],  # Much lower: AIR rarely bets 50%
}

# --- BET_100 probabilities ---
_BET_100_PROB = {
    "PREMIUM":      [0.20, 0.25, 0.28, 0.30],  # Premium polarizes toward big bets late
    "STRONG":       [0.15, 0.20, 0.22, 0.20],
    "MEDIUM":       [0.08, 0.12, 0.12, 0.10],
    "SPECULATIVE":  [0.06, 0.08, 0.10, 0.08],
    "TRASH":        [0.01, 0.02, 0.02, 0.02],
    # Postflop
    "STRONG_MADE":  [0.20, 0.28, 0.30, 0.32],  # Strong made hands overbet for value
    "MEDIUM_MADE":  [0.10, 0.15, 0.16, 0.14],
    "WEAK_MADE":    [0.04, 0.07, 0.07, 0.06],
    "STRONG_DRAW":  [0.10, 0.16, 0.18, 0.14],
    "WEAK_DRAW":    [0.03, 0.06, 0.06, 0.05],
    "AIR":          [0.00, 0.02, 0.02, 0.01],  # AIR almost never bets pot
}

# --- ALL_IN probabilities ---
_ALL_IN_PROB = {
    "PREMIUM":      [0.08, 0.12, 0.15, 0.18],
    "STRONG":       [0.05, 0.08, 0.10, 0.12],
    "MEDIUM":       [0.02, 0.03, 0.04, 0.04],
    "SPECULATIVE":  [0.03, 0.04, 0.06, 0.05],
    "TRASH":        [0.00, 0.01, 0.01, 0.01],
    # Postflop
    "STRONG_MADE":  [0.06, 0.10, 0.14, 0.18],
    "MEDIUM_MADE":  [0.03, 0.05, 0.07, 0.06],
    "WEAK_MADE":    [0.01, 0.02, 0.03, 0.03],
    "STRONG_DRAW":  [0.03, 0.06, 0.10, 0.08],
    "WEAK_DRAW":    [0.01, 0.02, 0.04, 0.03],
    "AIR":          [0.00, 0.01, 0.01, 0.01],
}


def _at_street(table: Dict, bucket: str, street: int) -> float:
    street = min(street, 3)
    v = table.get(bucket)
    if v is None:
        return 0.5
    return v[street] if isinstance(v, (list, tuple)) else v


def get_fold_probability(belief: Dict[str, float], game_state: Any) -> float:
    """P(fold) = sum over buckets of belief[bucket] * P(fold | bucket, street)."""
    street = min(game_state.street, 3)
    return sum(p * _at_street(_FOLD_PROB, bucket, street) for bucket, p in belief.items())


def get_call_probability(belief: Dict[str, float], game_state: Any) -> float:
    """P(call) = sum over buckets of belief[bucket] * P(call | bucket, street)."""
    street = min(game_state.street, 3)
    return sum(p * _at_street(_CALL_PROB, bucket, street) for bucket, p in belief.items())


def likelihood_action_given_bucket(action: str, bucket: str, street: int, opponent_type: str = TIGHT) -> float:
    """P(action | bucket, opponent_type, street)."""
    street = min(street, 3)
    # Opponent type scaling — more differentiated than before
    if opponent_type == TIGHT:
        fold_scale, call_scale, bet_scale = 1.30, 0.85, 0.65
    elif opponent_type == LOOSE:
        fold_scale, call_scale, bet_scale = 0.80, 1.15, 1.20
    else:  # AGGRESSIVE
        fold_scale, call_scale, bet_scale = 0.70, 0.95, 1.40

    if action == FOLD:
        return min(1.0, _at_street(_FOLD_PROB, bucket, street) * fold_scale)
    if action in (CHECK, CALL):
        return min(1.0, _at_street(_CALL_PROB, bucket, street) * call_scale)
    if action == BET_25:
        return min(1.0, _at_street(_BET_25_PROB, bucket, street) * bet_scale)
    if action == BET_50:
        return min(1.0, _at_street(_BET_50_PROB, bucket, street) * bet_scale)
    if action == BET_100:
        return min(1.0, _at_street(_BET_100_PROB, bucket, street) * bet_scale)
    if action == ALL_IN:
        return min(1.0, _at_street(_ALL_IN_PROB, bucket, street) * bet_scale)
    return 0.01