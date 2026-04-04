"""
Expected value calculator for each action given game state and optional belief.

FIX: In CALL/CHECK branch, the old code did:
    equity * final_pot - amount_invested - cost
amount_invested (all prior bets) is a sunk cost in EV terms — subtracting it
makes the agent falsely think calling is more expensive the more it has already invested,
which can cause it to fold when it shouldn't. Correct formula is:
    equity * final_pot - cost
where cost is only the current action's cost.
"""

from typing import Any, Dict, Optional

from engine.action_space import get_legal_actions, FOLD, CHECK, CALL, BET_25, BET_50, BET_100, ALL_IN
from evaluation.monte_carlo import estimate_equity


def _belief_cache_key(belief: Optional[Dict[str, float]]) -> Optional[tuple]:
    if belief is None:
        return None
    return tuple(sorted(((k, round(v, 6)) for k, v in belief.items()), key=lambda x: x[0]))


def _get_equity_cached(
    game_state: Any,
    hero_cards: list,
    board: list,
    belief: Optional[Dict[str, float]],
    samples: int,
    rng: Any,
    hero_id: int,
) -> tuple:
    cache = getattr(game_state, "_equity_cache", None)
    if cache is None:
        cache = {}
        setattr(game_state, "_equity_cache", cache)

    key = (
        hero_id,
        tuple(hero_cards),
        tuple(board),
        _belief_cache_key(belief),
        samples,
    )
    if key not in cache:
        cache[key] = estimate_equity(
            hero_cards,
            board,
            belief=belief,
            samples=samples,
            rng=rng,
        )
    return cache[key]


def compute_ev(
    action: str,
    game_state: Any,
    belief: Optional[Dict[str, float]] = None,
    hero_id: int = 0,
    samples: int = 200,
    rng: Any = None,
) -> float:
    """
    Compute EV for an action.

    Fold:        EV = 0  (relative; folding gains/loses nothing from this point)
    Call/Check:  EV = equity * final_pot - cost          (cost = chips going in NOW)
    Bet/Raise:   EV = fold_prob * pot + call_prob * (equity * final_pot - cost)

    Note: amount_invested is sunk and NOT subtracted — it cannot be recovered regardless
    of action, so it does not affect which action has highest EV.
    """
    pid = hero_id
    stacks = game_state.stacks
    pot = game_state.pot
    street_bets = getattr(game_state, "street_bets", [0.0, 0.0])
    my_bet_this_street = street_bets[pid]
    opp_bet_this_street = street_bets[1 - pid]
    to_call = max(0.0, opp_bet_this_street - my_bet_this_street)
    my_stack = stacks[pid]

    if action == FOLD:
        # EV = 0 relative to the current decision point (sunk costs excluded)
        return 0.0

    hero_cards = game_state.private_cards.get(pid, [])
    board = getattr(game_state, "board", [])

    if action == CHECK:
        cost = 0.0
        final_pot = pot
        win_prob, tie_prob = _get_equity_cached(
            game_state=game_state, hero_cards=hero_cards, board=board,
            belief=belief, samples=samples, rng=rng, hero_id=pid,
        )
        equity = win_prob + tie_prob * 0.5
        return equity * final_pot - cost  # FIX: removed - amount_invested

    if action == CALL:
        cost = min(my_stack, to_call)
        final_pot = pot + cost
        win_prob, tie_prob = _get_equity_cached(
            game_state=game_state, hero_cards=hero_cards, board=board,
            belief=belief, samples=samples, rng=rng, hero_id=pid,
        )
        equity = win_prob + tie_prob * 0.5
        return equity * final_pot - cost  # FIX: removed - amount_invested

    # Bet/raise actions
    pot_after_call = pot + to_call if to_call > 0 else pot
    if action == BET_25:
        bet_size = max(0.5, round(pot_after_call * 0.25, 2))
    elif action == BET_50:
        bet_size = max(0.5, round(pot_after_call * 0.5, 2))
    elif action == BET_100:
        bet_size = max(0.5, round(pot_after_call * 1.0, 2))
    else:  # ALL_IN
        bet_size = my_stack
    bet_size = min(bet_size, my_stack)
    cost = bet_size
    final_pot = pot + to_call + bet_size

    if belief is None or len(belief) == 0:
        fold_prob = 0.2
        call_prob = 0.8
    else:
        from belief.opponent_model import get_fold_probability, get_call_probability
        fold_prob = get_fold_probability(belief, game_state)
        call_prob = get_call_probability(belief, game_state)

    win_prob, tie_prob = _get_equity_cached(
        game_state=game_state, hero_cards=hero_cards, board=board,
        belief=belief, samples=samples, rng=rng, hero_id=pid,
    )
    equity = win_prob + tie_prob * 0.5

    ev_if_fold = pot          # opponent folds, we win the pot
    ev_if_call = equity * final_pot - cost  # FIX: removed - amount_invested
    return fold_prob * ev_if_fold + call_prob * ev_if_call