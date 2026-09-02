"""
Game engine: play one hand between two agents, return chip delta.
"""

# `from __future__ import annotations` keeps the `List[float] | Dict[str, Any]`
# return annotation below lazily-evaluated as a string, so this module stays
# importable on Python 3.8/3.9 (PEP 604 `X | Y` syntax at runtime requires 3.10+),
# matching the "Python 3.8+" requirement stated in the README.
from __future__ import annotations

import random
from typing import List, Optional, Any, Dict

from engine.cards import Deck
from engine.game_state import GameState
from engine.action_space import BB, get_legal_actions


def play_hand(
    agent1: Any,
    agent2: Any,
    seed: Optional[int] = None,
    evaluator: Optional[Any] = None,
    return_details: bool = False,
    forced_private_cards: Optional[Dict[int, List[Any]]] = None,
) -> List[float] | Dict[str, Any]:
    """
    Initialize state, deal cards, post blinds, alternate actions until terminal.
    Return chip delta for each player (e.g. [delta0, delta1]).
    If forced_private_cards is provided ({0: [Card, Card], 1: [Card, Card]}), 
    those cards are removed from the deck and dealt to the respective players.
    """
    rng = random.Random(seed)
    deck = Deck(rng=rng).build().shuffle()
    
    if forced_private_cards:
        # Pre-remove forced cards from the deck
        forced_strs = []
        for p_cards in forced_private_cards.values():
            for c in p_cards:
                forced_strs.append(str(c))
        
        filtered_cards = [c for c in deck.cards if str(c) not in forced_strs]
        deck.cards = filtered_cards
        private_cards = {0: forced_private_cards.get(0, deck.deal(2)),
                         1: forced_private_cards.get(1, deck.deal(2))}
    else:
        private_cards = {0: deck.deal(2), 1: deck.deal(2)}

    stacks = [50.0 * BB, 50.0 * BB]
    sb, bb = 0.5 * BB, BB
    stacks[0] -= sb
    stacks[1] -= bb
    pot = sb + bb

    state = GameState(
        stacks=stacks,
        pot=pot,
        street=0,
        board=[],
        private_cards=private_cards,
        current_player=0,
        betting_history=[],
        raises_this_street=0,
        last_bet_size=bb,
        terminal_flag=False,
        street_bets=[sb, bb],
        folded=None,
    )

    agents = [agent1, agent2]
    initial_stacks = [50.0 * BB, 50.0 * BB]

    while not state.is_terminal():
        pid = state.current_player
        legal = get_legal_actions(state, pid)
        if not legal:
            break
        # Capture the street the action was actually taken on BEFORE
        # apply_action(), since a CHECK/CALL that closes the street can
        # itself advance state.street as a side effect. Without this,
        # observers always see the (already-advanced) post-action street,
        # or - as was previously the case - no street at all, silently
        # defaulting to preflop for every belief update.
        acted_street = state.street
        action = agents[pid].act(state)
        if action not in legal:
            action = legal[0]
        state.apply_action(action)
        agents[1 - pid].observe(action, street=acted_street)

        # Deal next board cards when street advanced
        if state.street == 1 and len(state.board) == 0:
            state.board.extend(deck.deal(3))
        elif state.street == 2 and len(state.board) == 3:
            state.board.extend(deck.deal(1))
        elif state.street == 3 and len(state.board) == 4:
            state.board.extend(deck.deal(1))

    if state.folded is not None:
        winner = 1 - state.folded
        state.stacks[winner] += state.pot
        outcome = "fold"
        winner_id = winner
    elif evaluator is not None and state.street > 3:
        deltas = state.resolve_showdown(evaluator)
        state.stacks[0] += deltas[0]
        state.stacks[1] += deltas[1]
        if deltas[0] > deltas[1]:
            outcome = "showdown"
            winner_id = 0
        elif deltas[1] > deltas[0]:
            outcome = "showdown"
            winner_id = 1
        else:
            outcome = "tie"
            winner_id = None
    else:
        state.stacks[0] += state.pot / 2
        state.stacks[1] += state.pot / 2
        outcome = "tie"
        winner_id = None

    chip_delta = [state.stacks[0] - initial_stacks[0], state.stacks[1] - initial_stacks[1]]
    if not return_details:
        return chip_delta

    actions_by_player = {0: [], 1: []}
    for entry in state.betting_history:
        pid = entry.get("player_id")
        if pid in actions_by_player:
            actions_by_player[pid].append(entry.get("action"))

    return {
        "chip_delta": chip_delta,
        "outcome": outcome,
        "winner_id": winner_id,
        "board": list(state.board),
        "private_cards": dict(state.private_cards),
        "betting_history": list(state.betting_history),
        "actions_by_player": actions_by_player,
    }
