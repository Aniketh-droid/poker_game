"""
Hand bucketing: preflop (5 buckets) and postflop (6 buckets). Deterministic rule-based.
"""

from typing import List, Tuple

from engine.cards import Card

# Preflop buckets
PREMIUM = "PREMIUM"
STRONG = "STRONG"
MEDIUM = "MEDIUM"
SPECULATIVE = "SPECULATIVE"
TRASH = "TRASH"

# Postflop buckets
STRONG_MADE = "STRONG_MADE"
MEDIUM_MADE = "MEDIUM_MADE"
WEAK_MADE = "WEAK_MADE"
STRONG_DRAW = "STRONG_DRAW"
WEAK_DRAW = "WEAK_DRAW"
AIR = "AIR"


def _hand_ranks(hand: List[Card]) -> Tuple[int, int]:
    """Return (high, low) ranks sorted descending."""
    r1, r2 = hand[0][0], hand[1][0]
    return (max(r1, r2), min(r1, r2))


def _suited(hand: List[Card]) -> bool:
    return hand[0][1] == hand[1][1]


def _paired(hand: List[Card]) -> bool:
    return hand[0][0] == hand[1][0]


def classify_preflop(hand: List[Card]) -> str:
    """Classify 2-card hand into preflop bucket. Deterministic."""
    if len(hand) != 2:
        return TRASH
    high, low = _hand_ranks(hand)
    suited = _suited(hand)
    paired = _paired(hand)

    if paired:
        if high >= 12:
            return PREMIUM
        if high >= 10:
            return STRONG
        if high >= 7:
            return MEDIUM
        if high >= 4:
            return SPECULATIVE
        return TRASH

    if high == 14 and low >= 10:
        return PREMIUM
    if high == 14 and low >= 8:
        return STRONG
    if high >= 12 and low >= 10:
        return STRONG
    if high >= 11 and low >= 9:
        return STRONG
    if high >= 10 and low >= 8:
        return MEDIUM
    if high == 14 and low >= 6:
        return MEDIUM if suited else SPECULATIVE
    if high >= 9 and low >= 6 and suited:
        return MEDIUM
    if high >= 8 and low >= 5:
        return SPECULATIVE
    if high >= 7 and low >= 4 and suited:
        return SPECULATIVE
    return TRASH


def classify_postflop(hand: List[Card], board: List[Card]) -> str:
    """Classify hand into postflop bucket given board. Rule-based, deterministic."""
    if len(hand) != 2 or len(board) < 3:
        return classify_preflop(hand)

    from evaluation.hand_evaluator import evaluate_7card

    all_cards = hand + board
    score = evaluate_7card(all_cards)
    tier = score >> 20

    if tier >= 6:
        return STRONG_MADE
    if tier >= 3:
        return MEDIUM_MADE
    if tier >= 1:
        return WEAK_MADE

    high, low = _hand_ranks(hand)
    board_ranks = [c[0] for c in board]
    suited = _suited(hand)
    suit = hand[0][1]
    board_suits = [c[1] for c in board]
    flush_draw = 1 + board_suits.count(suit) >= 4
    gaps = sorted(set(high - r for r in board_ranks) | set(low - r for r in board_ranks))
    straight_draw = any(abs(g) <= 2 for g in gaps) or (high >= 12 and 14 in board_ranks)

    if flush_draw or straight_draw:
        return STRONG_DRAW if (flush_draw and high >= 10) or (straight_draw and high >= 10) else WEAK_DRAW
    return AIR
