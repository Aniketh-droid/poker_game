from typing import Any
from agents.base_agent import BaseAgent
from engine.action_space import get_legal_actions

class HumanAgent(BaseAgent):
    def __init__(self, player_id: int = 0):
        self.player_id = player_id

    def act(self, game_state: Any) -> str:
        legal = get_legal_actions(game_state, self.player_id)
        if not legal:
            return "FOLD"

        print(f"\n--- Street: {game_state.street} | Pot: {game_state.pot:.2f} ---")
        print(f"Board: {game_state.board}")
        print(f"Your Cards: {game_state.private_cards[self.player_id]}")
        print(f"Your Stack: {game_state.stacks[self.player_id]:.2f}")
        print(f"Opponent Stack: {game_state.stacks[1 - self.player_id]:.2f}")
        print(f"Legal Actions: {', '.join(legal)}")

        while True:
            action = input("Enter your action: ").strip().upper()
            if action in legal:
                return action
            print(f"Invalid action. Choose from: {', '.join(legal)}")
