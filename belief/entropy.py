"""
Entropy of a distribution: H = -Σ p log p.
"""

import math
from typing import Dict


def compute_entropy(distribution: Dict[str, float]) -> float:
    """H = -Σ p log p. Uses natural log."""
    h = 0.0
    for p in distribution.values():
        if p > 0:
            h -= p * math.log(p)
    return h
