"""
Strategy mixer: with probability epsilon choose random legal action, else argmax EV.
"""

import random
from typing import Dict, List, Any

from engine.action_space import get_legal_actions


def select_action(
    ev_dict: Dict[str, float],
    legal_actions: List[str],
    epsilon: float = 0.05,
    rng: random.Random = None,
) -> str:
    """
    With probability epsilon: choose random legal action.
    Else: choose action with maximum EV.
    """
    if rng is None:
        rng = random.Random()
    if not legal_actions:
        return "FOLD"
    if rng.random() < epsilon:
        return rng.choice(legal_actions)
    best_ev = max(ev_dict.get(a, float("-inf")) for a in legal_actions)
    best_actions = [a for a in legal_actions if ev_dict.get(a, float("-inf")) == best_ev]
    return rng.choice(best_actions)
