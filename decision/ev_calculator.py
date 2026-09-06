"""
Expected value calculator for each action given game state and optional belief.

FIX: In CALL/CHECK branch, the old code did:
    equity * final_pot - amount_invested - cost
amount_invested (all prior bets) is a sunk cost in EV terms — subtracting it
makes the agent falsely think calling is more expensive the more it has already invested,
which can cause it to fold when it shouldn't. Correct formula is:
    equity * final_pot - cost
where cost is only the current action's cost.

FIX: compute_ev() (the single-opponent path) used to read the opponent's
current-street bet via the hardcoded index `street_bets[1 - pid]`. That's
only correct when the two players occupy seats 0 and 1. EVAgent and
BayesianAgent both call this exact function whenever exactly one opponent is
still live -- which, at a 3-6 handed table, happens any time enough players
have folded to leave two live seats that AREN'T 0 and 1 (e.g. seats 2 and 4
heads-up after everyone else folds). `1 - pid` then reads a different,
often-folded seat's stale bet via Python's negative-index wraparound,
producing a wrong `to_call` and therefore a wrong EV for every action.
`_opponent_bet_this_street` below fixes this by asking game_state itself
who the live opponent actually is (falling back to the old `1 - pid` only
for legacy 2-only test doubles that don't implement live_players()).
"""

from typing import Any, Dict, List, Optional

from engine.action_space import get_legal_actions, FOLD, CHECK, CALL, BET_25, BET_50, BET_100, ALL_IN
from evaluation.monte_carlo import estimate_equity, estimate_equity_multiway


def _opponent_bet_this_street(game_state: Any, pid: int) -> float:
    """Return the sole live opponent's current-street bet, correctly identifying
    that opponent's seat even at a 3-6 handed table reduced to heads-up (rather
    than assuming seats 0/1 via a hardcoded `1 - pid`)."""
    street_bets = getattr(game_state, "street_bets", [0.0, 0.0])
    if hasattr(game_state, "live_players"):
        live_opponents = [i for i in game_state.live_players() if i != pid]
        if len(live_opponents) == 1:
            return street_bets[live_opponents[0]]
        if len(live_opponents) > 1:
            # compute_ev() is only meant to be called with <=1 live opponent;
            # defensively take the largest opposing bet rather than guessing.
            return max(street_bets[i] for i in live_opponents)
    # Legacy 2-only test doubles without live_players(): original assumption.
    return street_bets[1 - pid]


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
    opponent_stats: Optional[Any] = None,
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
    opp_bet_this_street = _opponent_bet_this_street(game_state, pid)
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

    if action == ALL_IN and to_call > 0 and my_stack <= to_call:
        # All-in for LESS than the amount needed to call: this is a capped call,
        # not a bet/raise -- hero isn't asking anyone to fold, just putting in
        # whatever's left. Route it through the CALL formula (cost = the whole
        # stack, not to_call + bet_size, which would double-count and wildly
        # overstate the pot) rather than the bet/raise branch below, which
        # assumes bet_size is calling PLUS an additional raise on top.
        cost = my_stack
        final_pot = pot + cost
        win_prob, tie_prob = _get_equity_cached(
            game_state=game_state, hero_cards=hero_cards, board=board,
            belief=belief, samples=samples, rng=rng, hero_id=pid,
        )
        equity = win_prob + tie_prob * 0.5
        return equity * final_pot - cost

    # Bet/raise actions
    pot_after_call = pot + to_call if to_call > 0 else pot
    if action == BET_25:
        bet_size = max(0.5, round(pot_after_call * 0.25, 2))
    elif action == BET_50:
        bet_size = max(0.5, round(pot_after_call * 0.5, 2))
    elif action == BET_100:
        bet_size = max(0.5, round(pot_after_call * 1.0, 2))
    else:  # ALL_IN (here, strictly more than to_call -- a genuine raise)
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
        if opponent_stats is not None:
            # Adaptive correction: shrink the static archetype prior toward
            # this opponent's actual observed fold/call frequency at this
            # street (see belief/opponent_stats.py). With no observations yet
            # this is a no-op; it only matters once the match has accumulated
            # real signal about an opponent the archetype table mismatches.
            from belief.opponent_stats import blend_with_prior
            empirical = opponent_stats.empirical_rates(game_state.street)
            fold_prob, call_prob = blend_with_prior(fold_prob, call_prob, empirical)

    win_prob, tie_prob = _get_equity_cached(
        game_state=game_state, hero_cards=hero_cards, board=board,
        belief=belief, samples=samples, rng=rng, hero_id=pid,
    )
    equity = win_prob + tie_prob * 0.5

    ev_if_fold = pot          # opponent folds, we win the pot
    ev_if_call = equity * final_pot - cost  # FIX: removed - amount_invested
    return fold_prob * ev_if_fold + call_prob * ev_if_call


def _opp_belief_cache_key(opp_belief_list: List[Optional[Dict[str, float]]]) -> tuple:
    return tuple(_belief_cache_key(b) for b in opp_belief_list)


def _get_equity_multiway_cached(
    game_state: Any,
    hero_cards: list,
    board: list,
    opp_belief_list: List[Optional[Dict[str, float]]],
    samples: int,
    rng: Any,
    hero_id: int,
) -> tuple:
    # Mirrors _get_equity_cached above: equity doesn't depend on which action
    # we're evaluating, only on hero cards/board/opponent beliefs, so without
    # this cache compute_ev_multiway's per-action call sites (CHECK/CALL/every
    # bet size) were each re-running a fresh samples=200-per-opponent Monte
    # Carlo -- 5-7x the necessary work per decision point, which is what made
    # multiway BayesianAgent decisions take 1-3+ seconds each at a 5-6 handed
    # table. One estimate per decision, reused across every candidate action.
    cache = getattr(game_state, "_equity_cache_multiway", None)
    if cache is None:
        cache = {}
        setattr(game_state, "_equity_cache_multiway", cache)

    key = (hero_id, tuple(hero_cards), tuple(board), _opp_belief_cache_key(opp_belief_list), samples)
    if key not in cache:
        cache[key] = estimate_equity_multiway(
            hero_cards, board, opp_belief_list, samples=samples, rng=rng,
        )
    return cache[key]


def compute_ev_multiway(
    action: str,
    game_state: Any,
    hero_id: int,
    opponent_beliefs: Optional[Dict[int, Optional[Dict[str, float]]]] = None,
    opponent_fold_probs: Optional[Dict[int, float]] = None,
    samples: int = 200,
    rng: Any = None,
) -> float:
    """
    EV for `action` at an N-handed table (2 to 6 players), used by any agent seated
    where more than one opponent may still be live. Reuses the same fold/call
    structure as compute_ev() above but generalized:

    - equity is estimated multiway (hero vs every currently-live opponent at once)
      via evaluation.monte_carlo.estimate_equity_multiway, keyed by each live
      opponent's own belief (opponent_beliefs[seat], or None for a
      non-belief-tracking opponent -- sampled uniformly).
    - a bet/raise's "does everyone fold" probability is the PRODUCT of each live
      opponent's individual fold probability (opponent_fold_probs[seat], default
      0.2 per opponent if not supplied). This is a deliberate simplification, not
      a full N-player game-theoretic solve (real multiway solves need CFR-style
      search over every opponent's response, not just "fold or not") -- but it's
      the right tradeoff for a real-time, fun-first game bot: it captures the
      intuitive shape (more live opponents -> harder to bluff everyone off a
      hand -> lower fold equity) without needing a full solver in the hot path.
    """
    pid = hero_id
    stacks = game_state.stacks
    pot = game_state.pot
    live = [i for i in game_state.live_players() if i != pid] if hasattr(game_state, "live_players") \
        else [i for i in range(len(stacks)) if i != pid]
    street_bets = getattr(game_state, "street_bets", [0.0] * len(stacks))
    max_bet = max((street_bets[i] for i in live + [pid]), default=street_bets[pid])
    to_call = max(0.0, max_bet - street_bets[pid])
    my_stack = stacks[pid]

    if action == FOLD:
        return 0.0

    hero_cards = game_state.private_cards.get(pid, [])
    board = getattr(game_state, "board", [])
    beliefs = opponent_beliefs or {}
    opp_belief_list = [beliefs.get(i) for i in live]

    def _equity() -> float:
        win_prob, tie_prob = _get_equity_multiway_cached(
            game_state=game_state, hero_cards=hero_cards, board=board,
            opp_belief_list=opp_belief_list, samples=samples, rng=rng, hero_id=pid,
        )
        return win_prob + tie_prob * 0.5

    if action == CHECK:
        return _equity() * pot - 0.0

    if action == CALL:
        cost = min(my_stack, to_call)
        final_pot = pot + cost
        return _equity() * final_pot - cost

    if action == ALL_IN and to_call > 0 and my_stack <= to_call:
        # Capped call, not a bet/raise -- see the matching comment in compute_ev().
        cost = my_stack
        final_pot = pot + cost
        return _equity() * final_pot - cost

    # Bet/raise
    pot_after_call = pot + to_call if to_call > 0 else pot
    if action == BET_25:
        bet_size = max(0.5, round(pot_after_call * 0.25, 2))
    elif action == BET_50:
        bet_size = max(0.5, round(pot_after_call * 0.5, 2))
    elif action == BET_100:
        bet_size = max(0.5, round(pot_after_call * 1.0, 2))
    else:  # ALL_IN (here, strictly more than to_call -- a genuine raise)
        bet_size = my_stack
    bet_size = min(bet_size, my_stack)
    cost = bet_size
    final_pot = pot + to_call + bet_size

    fold_probs = opponent_fold_probs or {}
    fold_prob_all = 1.0
    for i in live:
        fold_prob_all *= fold_probs.get(i, 0.2)
    call_prob_any = 1.0 - fold_prob_all

    equity = _equity()
    ev_if_all_fold = pot
    ev_if_someone_continues = equity * final_pot - cost
    return fold_prob_all * ev_if_all_fold + call_prob_any * ev_if_someone_continues