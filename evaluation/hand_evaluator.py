"""
7-card hand evaluation. Returns strictly comparable integer ranks.
Order: High card, Pair, Two pair, Trips, Straight, Flush, Full house, Quads, Straight flush.
"""

from itertools import combinations
from typing import List, Tuple

from engine.cards import Card


def _rank_count(cards: List[Card]) -> List[Tuple[int, int]]:
    """Return list of (rank, count) sorted by count desc then rank desc."""
    counts = {}
    for r, s in cards:
        counts[r] = counts.get(r, 0) + 1
    return sorted(((r, c) for r, c in counts.items()), key=lambda x: (-x[1], -x[0]))


def _suit_count(cards: List[Card]) -> List[Tuple[int, int]]:
    """Return list of (suit, count) sorted by count desc."""
    counts = {}
    for r, s in cards:
        counts[s] = counts.get(s, 0) + 1
    return sorted(((s, c) for s, c in counts.items()), key=lambda x: -x[1])


def _straight_high(ranks: List[int]) -> int:
    """High card of best straight, or 0."""
    ranks = sorted(set(ranks), reverse=True)
    for i in range(len(ranks) - 4):
        if ranks[i] - ranks[i + 4] == 4:
            return ranks[i]
    if 14 in ranks:
        low = [r if r != 14 else 1 for r in ranks]
        low.sort(reverse=True)
        for i in range(len(low) - 4):
            if low[i] - low[i + 4] == 4:
                return 5
    return 0


def evaluate_7card(cards: List[Card]) -> int:
    """
    Evaluate best 5-card hand from 7 cards. Return integer rank (higher = better).
    Hand tiers (high bits): 8=SF, 7=Quads, 6=FH, 5=Flush, 4=Straight, 3=Trips, 2=Two pair, 1=Pair, 0=High.
    """
    if len(cards) < 5:
        return 0
    if len(cards) > 7:
        cards = cards[:7]
    best = 0
    for five in combinations(cards, 5):
        v = _eval5(list(five))
        if v > best:
            best = v
    return best


def _eval5(cards: List[Card]) -> int:
    """Evaluate exactly 5 cards. Single integer rank."""
    category_scale = 1_000_000

    def encode(vals: List[int]) -> int:
        # Base-15 encoding keeps lexical card-rank ordering within a category.
        out = 0
        for v in vals:
            out = out * 15 + v
        return out

    ranks = [c[0] for c in cards]
    rank_counts = _rank_count(cards)
    suit_counts = _suit_count(cards)
    flush = suit_counts[0][1] >= 5
    straight_high = _straight_high(ranks)

    if flush and straight_high:
        return 8 * category_scale + encode([straight_high])
    if rank_counts[0][1] == 4:
        quad_r = rank_counts[0][0]
        kicker = max(r for r, _ in rank_counts if r != quad_r) if len(rank_counts) > 1 else 0
        return 7 * category_scale + encode([quad_r, kicker])
    if rank_counts[0][1] >= 3 and len(rank_counts) >= 2 and rank_counts[1][1] >= 2:
        trip_r = rank_counts[0][0]
        pair_r = rank_counts[1][0]
        return 6 * category_scale + encode([trip_r, pair_r])
    if flush:
        high = sorted(ranks, reverse=True)[:5]
        return 5 * category_scale + encode(high)
    if straight_high:
        return 4 * category_scale + encode([straight_high])
    if rank_counts[0][1] == 3:
        trip_r = rank_counts[0][0]
        kickers = sorted((r for r, c in rank_counts if r != trip_r), reverse=True)[:2]
        return 3 * category_scale + encode([trip_r] + kickers)
    if rank_counts[0][1] == 2 and len(rank_counts) >= 2 and rank_counts[1][1] == 2:
        p1, p2 = rank_counts[0][0], rank_counts[1][0]
        high, low = max(p1, p2), min(p1, p2)
        kicker = rank_counts[2][0] if len(rank_counts) > 2 else 0
        return 2 * category_scale + encode([high, low, kicker])
    if rank_counts[0][1] == 2:
        pair_r = rank_counts[0][0]
        kickers = sorted((r for r, c in rank_counts if r != pair_r), reverse=True)[:3]
        return 1 * category_scale + encode([pair_r] + kickers)
    high = sorted(ranks, reverse=True)[:5]
    return 0 * category_scale + encode(high)


def compare(hand1: List[Card], hand2: List[Card]) -> int:
    """
    Compare two hands (each 5+ cards). Return >0 if hand1 wins, <0 if hand2 wins, 0 if tie.
    """
    v1 = evaluate_7card(hand1)
    v2 = evaluate_7card(hand2)
    return v1 - v2
