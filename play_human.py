import traceback
from agents.human_agent import HumanAgent
from agents.ev_agent import EVAgent
from agents.random_agent import RandomAgent
from agents.bayesian_agent import BayesianAgent
from engine.game_engine import play_hand
from engine.cards import Card

def parse_hand(hand_str: str) -> list:
    if not hand_str.strip():
        return []
    cards = []
    for cstr in hand_str.strip().split():
        if len(cstr) == 2:
            rank_char = cstr[0].upper()
            suit_char = cstr[1].lower()
            
            # Map input suit to int (0-3)
            suit_map = {'h': 0, 'd': 1, 's': 2, 'c': 3}
            # Map rank to correctly formatted int (2-14)
            rank_map = {'A': 14, 'K': 13, 'Q': 12, 'J': 11, 'T': 10}
            
            if rank_char in rank_map:
                rank = rank_map[rank_char]
            elif rank_char.isdigit() and 2 <= int(rank_char) <= 9:
                rank = int(rank_char)
            else:
                print(f"Invalid rank in {cstr}")
                continue
                
            suit = suit_map.get(suit_char)
            if suit is not None:
                cards.append((rank, suit))
            else:
                print(f"Invalid suit in {cstr}")
    return cards

def main():
    print("=== Poker Interactive Mode ===")
    print("Choose your opponent:")
    print("1: Random Agent")
    print("2: EV Agent")
    print("3: Bayesian Agent")
    
    opp_choice = input("Enter choice (1/2/3): ").strip()
    
    print("\nDo you want to rig your cards?")
    print("Enter 2 cards (e.g. 'Ah Kd' for Ace of Hearts and King of Diamonds) or leave blank for a random hand.")
    hand_str = input("Your cards: ").strip()
    
    forced_cards = None
    if hand_str:
        try:
            cards = parse_hand(hand_str)
            if len(cards) == 2:
                forced_cards = {0: cards}
                print(f"Hand rigged to: {cards[0]}, {cards[1]}")
            else:
                print("Invalid hand format. Proceeding with random cards.")
        except Exception as e:
            traceback.print_exc()
            print("Failed to parse cards. Proceeding with random cards.")

    # Instantiate agents
    hero = HumanAgent(player_id=0)
    
    if opp_choice == '1':
        villain = RandomAgent(player_id=1)
        name = "RandomAgent"
    elif opp_choice == '2':
        villain = EVAgent(player_id=1, epsilon=0.0, samples=50) # No exploration, full strength
        name = "EVAgent"
    else:
        villain = BayesianAgent(player_id=1, opponent_type="TIGHT", samples=50)
        name = "BayesianAgent"

    print(f"\nStarting match against {name}...\n")
    
    try:
        from evaluation.hand_evaluator import compare as compare_hands
        evaluator = type("Eval", (), {"compare": staticmethod(compare_hands)})()
        
        result = play_hand(hero, villain, evaluator=evaluator, return_details=True, forced_private_cards=forced_cards)
        
        print("\n=== Hand Finished ===")
        print(f"Outcome: {result['outcome']}")
        print(f"Board: {result['board']}")
        print(f"Your Cards: {result['private_cards'][0]}")
        print(f"Opponent Cards: {result['private_cards'][1]}")
        print(f"Chip Deltas: You: {result['chip_delta'][0]:.2f}, Opponent: {result['chip_delta'][1]:.2f}")
        
    except Exception as e:
        traceback.print_exc()
        print(f"Error playing hand: {e}")

if __name__ == "__main__":
    main()
