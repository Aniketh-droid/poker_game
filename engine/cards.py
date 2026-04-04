"""
Card representation and Deck for heads-up No-Limit Texas Hold'em.
Card: (rank, suit), rank 2-14 (14=Ace), suit 0-3.
No external libraries.
"""

import random
from typing import List, Tuple

Card = Tuple[int, int]


def build_deck() -> List[Card]:
    """Build a standard 52-card deck. Rank 2-14, suit 0-3."""
    return [(r, s) for r in range(2, 15) for s in range(4)]


class Deck:
    """A 52-card deck with shuffle and deal. No external libs."""

    def __init__(self, rng: random.Random = None):
        self._rng = rng if rng is not None else random
        self._cards: List[Card] = []

    def build(self) -> "Deck":
        """Build/reset the deck to 52 cards."""
        self._cards = build_deck()
        return self

    def shuffle(self) -> "Deck":
        """Shuffle the deck in place."""
        self._rng.shuffle(self._cards)
        return self

    def deal(self, n: int) -> List[Card]:
        """Deal n cards from the top. Raises if not enough cards."""
        if n > len(self._cards):
            raise ValueError(f"Cannot deal {n} cards, only {len(self._cards)} left")
        out = self._cards[:n]
        self._cards = self._cards[n:]
        return out

    def __len__(self) -> int:
        return len(self._cards)
