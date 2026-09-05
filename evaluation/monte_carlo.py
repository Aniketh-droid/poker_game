"""
Monte Carlo equity estimation. Sample opponent hands (uniform or from belief), evaluate showdown.
"""

import random
from typing import List, Optional, Dict, Any

from engine.cards import Card, build_deck
from evaluation.hand_evaluator import evaluate_7card, compare


def _remaining_deck(hero_cards: List[Card], board: List[Card], opp_cards: Optional[List[Card]] = None) -> List[Card]:
    """Return deck minus hero cards, board, and optional opponent cards."""
    used = set(hero_cards) | set(board)
    if opp_cards:
        used |= set(opp_cards)
    return [c for c in build_deck() if c not in used]


def estimate_equity(
    hero_cards: List[Card],
    board: List[Card],
    belief: Optional[Dict[str, float]] = None,
    samples: int = 1000,
    rng: Optional[random.Random] = None,
) -> tuple:
    """
    Estimate win/tie probability for hero.
    If belief is None: sample opponent hand uniformly from remaining deck.
    If belief provided: sample bucket from belief, then sample hand from bucket.
    Returns (win_prob, tie_prob).
    """
    if rng is None:
        rng = random.Random()
    wins = ties = 0
    n = 0

    for _ in range(samples):
        if belief is not None:
            buckets = list(belief.keys())
            weights = [belief[b] for b in buckets]
            total = sum(weights)
            if total <= 0:
                opp_hand = _sample_uniform_opponent(hero_cards, board, rng)
            else:
                r = rng.uniform(0, total)
                for i, w in enumerate(weights):
                    r -= w
                    if r <= 0:
                        bucket = buckets[i]
                        opp_hand = _sample_hand_from_bucket(bucket, hero_cards, board, rng)
                        break
                else:
                    opp_hand = _sample_uniform_opponent(hero_cards, board, rng)
        else:
            opp_hand = _sample_uniform_opponent(hero_cards, board, rng)

        deck = _remaining_deck(hero_cards, board, opp_hand)
        need = 5 - len(board)
        if len(deck) < need:
            continue
        board_complete = list(board) + rng.sample(deck, need)
        hero_hand = hero_cards + board_complete
        opp_full = opp_hand + board_complete
        cmp = compare(hero_hand, opp_full)
        if cmp > 0:
            wins += 1
        elif cmp == 0:
            ties += 1
        n += 1

    if n == 0:
        return 0.0, 0.0
    return wins / n, ties / n


def _sample_uniform_opponent(hero_cards: List[Card], board: List[Card], rng: random.Random) -> List[Card]:
    """Sample 2 cards uniformly from deck excluding hero and board."""
    deck = _remaining_deck(hero_cards, board)
    if len(deck) < 2:
        return []
    return rng.sample(deck, 2)


def _sample_hand_from_bucket(
    bucket: str,
    hero_cards: List[Card],
    board: List[Card],
    rng: random.Random,
) -> List[Card]:
    """Sample a random 2-card hand that falls in the given bucket. Fallback to uniform."""
    return _sample_hand_from_bucket_excluding(bucket, list(hero_cards) + list(board), board, rng)


def _sample_hand_from_bucket_excluding(
    bucket: str,
    used_cards: List[Card],
    board: List[Card],
    rng: random.Random,
) -> List[Card]:
    """Sample a random 2-card hand in `bucket`, excluding every card in used_cards
    (hero + board + any other players' hands already dealt this Monte Carlo sample).
    Fallback to uniform among the remaining deck."""
    from belief.hand_bucketing import classify_preflop, classify_postflop

    used = set(used_cards)
    deck = [c for c in build_deck() if c not in used]
    if len(deck) < 2:
        return []
    for _ in range(200):
        hand = rng.sample(deck, 2)
        if len(board) < 3:
            if classify_preflop(hand) == bucket:
                return hand
        else:
            if classify_postflop(hand, board) == bucket:
                return hand
    return rng.sample(deck, 2)


def estimate_equity_multiway(
    hero_cards: List[Card],
    board: List[Card],
    opponent_beliefs: List[Optional[Dict[str, float]]],
    samples: int = 1000,
    rng: Optional[random.Random] = None,
) -> tuple:
    """
    N-way equity: hero vs len(opponent_beliefs) live opponents at once (a 3-6 handed
    table). Each opponent's hole cards are sampled independently from that opponent's
    own belief distribution (pass None for an opponent with no belief model, e.g. a
    RandomAgent/TightAgent-style villain -- sampled uniformly instead), with each
    sample respecting every card already dealt earlier in the same round (hero, board,
    and any opponents sampled before it) so no two players are ever dealt the same card.

    Returns (win_prob, tie_prob) for hero, where "win" means hero's hand beats every
    sampled opponent hand outright and "tie" means hero shares the best hand with at
    least one opponent and nobody beats hero.
    """
    if rng is None:
        rng = random.Random()
    if not opponent_beliefs:
        return estimate_equity(hero_cards, board, belief=None, samples=samples, rng=rng)

    wins = ties = 0
    n = 0

    for _ in range(samples):
        used: List[Card] = list(hero_cards) + list(board)
        opp_hands: List[List[Card]] = []
        sample_ok = True

        for belief in opponent_beliefs:
            deck = [c for c in build_deck() if c not in used]
            if len(deck) < 2:
                sample_ok = False
                break
            hand = None
            if belief:
                buckets = list(belief.keys())
                weights = [belief[b] for b in buckets]
                total = sum(weights)
                if total > 0:
                    r = rng.uniform(0, total)
                    for i, w in enumerate(weights):
                        r -= w
                        if r <= 0:
                            hand = _sample_hand_from_bucket_excluding(buckets[i], used, board, rng)
                            break
            if not hand:
                hand = rng.sample(deck, 2)
            opp_hands.append(hand)
            used.extend(hand)

        if not sample_ok:
            continue

        deck = [c for c in build_deck() if c not in used]
        need = 5 - len(board)
        if len(deck) < need:
            continue
        board_complete = list(board) + rng.sample(deck, need)
        hero_full = hero_cards + board_complete

        beaten = False
        tied = False
        for oh in opp_hands:
            cmp = compare(hero_full, oh + board_complete)
            if cmp < 0:
                beaten = True
                break
            elif cmp == 0:
                tied = True
        if not beaten:
            if tied:
                ties += 1
            else:
                wins += 1
        n += 1

    if n == 0:
        return 0.0, 0.0
    return wins / n, ties / n
