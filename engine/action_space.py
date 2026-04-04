"""
Action space for heads-up No-Limit Texas Hold'em.
Bet sizes: 25%, 50%, 100% pot, or all-in. Max 2 raises per street.
"""

from typing import List, Any

# Action constants
FOLD = "FOLD"
CHECK = "CHECK"
CALL = "CALL"
BET_25 = "BET_25"
BET_50 = "BET_50"
BET_100 = "BET_100"
ALL_IN = "ALL_IN"

# All bet/raise actions for raise cap logic
BET_ACTIONS = {BET_25, BET_50, BET_100, ALL_IN}

# Big blind in chips (1 BB)
BB = 1


def get_legal_actions(game_state: Any, player_id: int) -> List[str]:
    """
    Return list of legal actions for the current player.
    Enforces raise cap (max 2 raises per street), stack limits, and prevents illegal check/call.
    """
    if hasattr(game_state, "_update_to_call"):
        game_state._update_to_call()
    stacks = game_state.stacks
    pot = game_state.pot
    raises_this_street = game_state.raises_this_street
    last_bet_size = game_state.last_bet_size
    street_bets = getattr(game_state, "street_bets", [0.0, 0.0])
    my_bet_this_street = street_bets[player_id]
    opp_bet_this_street = street_bets[1 - player_id]
    to_call = opp_bet_this_street - my_bet_this_street
    if to_call < 0:
        to_call = 0.0

    my_stack = stacks[player_id]
    legal = []

    if to_call > 0:
        legal.append(FOLD)
    if to_call == 0:
        legal.append(CHECK)
    if to_call > 0 and my_stack >= to_call:
        legal.append(CALL)

    if raises_this_street >= 2:
        return legal

    min_raise = max(last_bet_size, BB)
    pot_after_call = pot + to_call if to_call > 0 else pot

    bet_25_size = max(min_raise, round(pot_after_call * 0.25, 2))
    bet_50_size = max(min_raise, round(pot_after_call * 0.5, 2))
    bet_100_size = max(min_raise, round(pot_after_call * 1.0, 2))

    if my_stack >= bet_25_size and bet_25_size > my_bet_this_street:
        legal.append(BET_25)
    if my_stack >= bet_50_size and bet_50_size > my_bet_this_street and BET_50 not in legal:
        legal.append(BET_50)
    if my_stack >= bet_100_size and bet_100_size > my_bet_this_street and BET_100 not in legal:
        legal.append(BET_100)
    if my_stack > 0 and my_stack > to_call:
        legal.append(ALL_IN)

    return legal
