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
    match starts; act() combines that with the live game_state to publish a
    `players` snapshot the frontend can render a whole table from, not just
    one opponent. Other seats' hole cards are never put in shared_state here
    -- they stay server-side until the match loop reveals them at showdown.
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

        n = len(game_state.stacks)
        folded = game_state.folded if hasattr(game_state, "folded") else set()
        all_in = getattr(game_state, "all_in", set())
        street_bets = getattr(game_state, "street_bets", [0.0] * n)

        players = []
        for i in range(n):
            meta = self.seat_meta[i] if i < len(self.seat_meta) else {}
            players.append({
                "seat": i,
                "is_hero": i == self.player_id,
                "key": meta.get("key"),
                "name": meta.get("name"),
                "avatar": meta.get("avatar"),
                "stack": game_state.stacks[i],
                "street_bet": street_bets[i] if i < len(street_bets) else 0.0,
                "folded": i in folded,
                "all_in": i in all_in,
            })

        self.shared_state["waiting_for_human"] = True
        self.shared_state["street"] = game_state.street
        self.shared_state["pot"] = game_state.pot
        self.shared_state["board"] = [str(c) for c in game_state.board]
        self.shared_state["hero_cards"] = [str(c) for c in game_state.private_cards.get(self.player_id, [])]
        self.shared_state["players"] = players
        self.shared_state["legal_actions"] = legal
        self.shared_state["to_call"] = getattr(game_state, "to_call", 0.0)
        self.shared_state["button"] = getattr(game_state, "button", 0)
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
