from typing import Any, Dict, List
import threading
from agents.base_agent import BaseAgent
from engine.action_space import get_legal_actions


class WebHumanAgent(BaseAgent):
    """
    An agent that waits for a web UI to provide an action.
    It takes a shared_state dict and an action_event (threading.Event).
    When act() is called, it updates the shared_state with the game context,
    blocks on the action_event, and then retrieves the action from shared_state.

    MULTIWAY: generalized from a single "villain" to an N-seat (2-6) table.
    `seat_meta` is a fixed list (indexed by seat) of {key, name, avatar} for
    every seat at the table, supplied once by the caller (app.py) when the
    match starts. Other seats' hole cards are never put in shared_state here
    -- they stay server-side until the match loop reveals them at showdown.

    Note: the full `players` table snapshot (stacks, bets, folded/all-in,
    SB/BB seats) is published by app.py's per-seat wrapper via
    `_publish_table_snapshot()` immediately before this act() runs for every
    seat, hero included -- so this class only needs to add the fields unique
    to the human's own turn (legal actions, hero's own cards, the waiting
    flag) rather than rebuilding the whole table view a second time here.
    """

    def __init__(self, player_id: int, shared_state: dict, action_event: threading.Event, seat_meta: List[Dict]):
        self.player_id = player_id
        self.shared_state = shared_state
        self.action_event = action_event
        self.seat_meta = seat_meta

    def act(self, game_state: Any) -> str:
        legal = get_legal_actions(game_state, self.player_id)
        if not legal:
            return "FOLD"

        self.shared_state["waiting_for_human"] = True
        self.shared_state["hero_cards"] = [str(c) for c in game_state.private_cards.get(self.player_id, [])]
        self.shared_state["legal_actions"] = legal
        self.shared_state["current_seat"] = self.player_id

        # Clear any previous action
        self.shared_state["human_action"] = None
        self.action_event.clear()

        # Block until the web UI sets the action and event
        self.action_event.wait()

        self.shared_state["waiting_for_human"] = False
        action = self.shared_state.get("human_action", "FOLD")

        if action not in legal:
            # Fallback if UI sends something weird
            action = legal[0]

        return action
