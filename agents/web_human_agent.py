from typing import Any
import threading
from agents.base_agent import BaseAgent
from engine.action_space import get_legal_actions

class WebHumanAgent(BaseAgent):
    """
    An agent that waits for a web UI to provide an action.
    It takes a shared_state dict and an action_event (threading.Event).
    When act() is called, it updates the shared_state with the game context,
    blocks on the action_event, and then retrieves the action from shared_state.
    """
    def __init__(self, player_id: int, shared_state: dict, action_event: threading.Event):
        self.player_id = player_id
        self.shared_state = shared_state
        self.action_event = action_event

    def act(self, game_state: Any) -> str:
        legal = get_legal_actions(game_state, self.player_id)
        if not legal:
            return "FOLD"

        # Update shared state so the UI knows what to display
        self.shared_state["waiting_for_human"] = True
        self.shared_state["street"] = game_state.street
        self.shared_state["pot"] = game_state.pot
        self.shared_state["board"] = [str(c) for c in game_state.board]
        self.shared_state["hero_cards"] = [str(c) for c in game_state.private_cards.get(self.player_id, [])]
        self.shared_state["villain_cards"] = [str(c) for c in game_state.private_cards.get(1 - self.player_id, [])] # Kept secretly in backend until showdown
        self.shared_state["hero_stack"] = game_state.stacks[self.player_id]
        self.shared_state["villain_stack"] = game_state.stacks[1 - self.player_id]
        self.shared_state["legal_actions"] = legal
        
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
