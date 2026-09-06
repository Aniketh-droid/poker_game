"""
Action space for N-handed (2-6 players) No-Limit Texas Hold'em.
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
    Generalized to N players: "the opponent's bet" becomes "the largest bet among live
    (non-folded) players" -- at num_players == 2 this is identical to the old behavior.
    """
    if hasattr(game_state, "_update_to_call"):
        game_state._update_to_call()
    stacks = game_state.stacks
    pot = game_state.pot
    raises_this_street = game_state.raises_this_street
    last_bet_size = game_state.last_bet_size
    street_bets = getattr(game_state, "street_bets", [0.0, 0.0])
    my_bet_this_street = street_bets[player_id]

    live_players = game_state.live_players() if hasattr(game_state, "live_players") else \
        [i for i in range(len(street_bets)) if i != getattr(game_state, "folded", None)]
    max_bet_this_street = max((street_bets[i] for i in live_players), default=my_bet_this_street)
    to_call = max_bet_this_street - my_bet_this_street
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

    # BUG FIX: an all-in for LESS than the call amount (0 < my_stack < to_call)
    # is a capped call, not a raise -- a short-stacked player must always be
    # able to shove their remaining chips. It used to require `my_stack >
    # to_call`, which covers only an all-in RAISE; a short-stacked player who
    # couldn't fully call (blocked from CALL above too) got NEITHER action,
    # leaving only FOLD. Handled here, before the raise-cap check below, since
    # a capped call doesn't reopen betting and must stay legal even after the
    # raise cap is hit -- unlike an all-in raise, which the cap should still
    # block (see the ALL_IN-as-raise case further down).
    if to_call > 0 and 0 < my_stack < to_call:
        legal.append(ALL_IN)

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
    # All-in as a RAISE (strictly more than to_call): a genuine raise, so it's
    # correctly gated by the raise cap via the early return above. (my_stack ==
    # to_call exactly is deliberately excluded here too -- CALL already covers
    # that case, no need for a redundant identical ALL_IN button.)
    if my_stack > 0 and my_stack > to_call:
        legal.append(ALL_IN)

    return legal
