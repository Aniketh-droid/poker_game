import threading
from flask import Flask, jsonify, request, send_from_directory
import traceback

from agents.web_human_agent import WebHumanAgent
from agents.ev_agent import EVAgent
from agents.random_agent import RandomAgent
from agents.bayesian_agent import BayesianAgent
from engine.game_engine import play_hand

app = Flask(__name__, static_folder='static', static_url_path='')

# Global state for communication between web thread and engine thread
shared_state = {
    "waiting_for_human": False,
    "human_action": None,
    "street": 0,
    "pot": 0,
    "board": [],
    "hero_cards": [],
    "villain_cards": [],
    "hero_stack": 0,
    "villain_stack": 0,
    "legal_actions": [],
    "game_over": False,
    "last_result": None,
    "villain_thoughts": []
}
action_event = threading.Event()
engine_thread = None

def run_engine_thread(opponent_type):
    global shared_state, action_event
    hero = WebHumanAgent(player_id=0, shared_state=shared_state, action_event=action_event)
    
    if opponent_type == 'RANDOM':
        villain = RandomAgent(player_id=1)
    elif opponent_type == 'EV':
        villain = EVAgent(player_id=1, epsilon=0.0, samples=50)
    else:  # BAYESIAN
        villain = BayesianAgent(player_id=1, opponent_type="TIGHT", samples=50)

    # Wrap the villain's act method to capture their thought process
    original_act = villain.act
    def wrapped_act(state):
        action = original_act(state)
        thought = f"Chose <strong>{action}</strong>."
        if hasattr(villain, '_last_ev_dict'):
            # clean up ev dict for display
            evs = " | ".join([f"{a}: {ev:.2f}" for a, ev in villain._last_ev_dict.items()])
            thought += f" <br><span style='color: #64748b; font-size: 0.85em'>Expected Values: [{evs}]</span>"
        if hasattr(villain, '_last_entropy'):
            thought += f" <br><span style='color: #ea580c; font-size: 0.85em'>Uncertainty (Entropy): {villain._last_entropy:.2f}</span>"
            
        shared_state.setdefault("villain_thoughts", []).append(f"<b>Street {state.street}</b>: {thought}")
        return action
    villain.act = wrapped_act

    try:
        from evaluation.hand_evaluator import compare as compare_hands
        evaluator = type("Eval", (), {"compare": staticmethod(compare_hands)})()
        result = play_hand(hero, villain, evaluator=evaluator, return_details=True)
        
        # Once hand is over
        shared_state["game_over"] = True
        shared_state["waiting_for_human"] = False
        
        # Map tuples like (14, 0) to standard string for frontend if array
        if result and "private_cards" in result:
            shared_state["villain_cards"] = [str(c) for c in result["private_cards"][1]]
            shared_state["board"] = [str(c) for c in result["board"]]
            
        shared_state["last_result"] = {
            "outcome": result["outcome"],
            "chip_delta": result["chip_delta"]
        }
        
    except Exception as e:
        traceback.print_exc()
        shared_state["game_over"] = True
        shared_state["waiting_for_human"] = False


@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/start', methods=['POST'])
def start_game():
    global engine_thread, shared_state, action_event
    opponent = request.json.get("opponent", "BAYESIAN")
    
    # Reset state
    shared_state.update({
        "waiting_for_human": False,
        "human_action": None,
        "street": 0, "pot": 0, "board": [], "hero_cards": [], "villain_cards": [],
        "hero_stack": 0, "villain_stack": 0, "legal_actions": [],
        "game_over": False, "last_result": None, "villain_thoughts": []
    })
    action_event.clear()
    
    engine_thread = threading.Thread(target=run_engine_thread, args=(opponent,), daemon=True)
    engine_thread.start()
    return jsonify({"status": "started"})
    
@app.route('/api/state', methods=['GET'])
def get_state():
    return jsonify(shared_state)
    
@app.route('/api/action', methods=['POST'])
def handle_action():
    global shared_state, action_event
    if not shared_state["waiting_for_human"]:
        return jsonify({"error": "Not waiting for action"}), 400
        
    action = request.json.get("action")
    if action not in shared_state["legal_actions"]:
        return jsonify({"error": "Invalid action"}), 400
        
    shared_state["human_action"] = action
    action_event.set()
    return jsonify({"status": "ok"})

@app.route('/api/simulate', methods=['POST'])
def run_simulation():
    matchup = request.json.get("matchup", "bayesian_vs_ev")
    hands = int(request.json.get("hands", 100))
    seeds = [12345]  # keeping it fast for web ui
    samples = 25
    
    from main import _run_pairing
    from agents.bayesian_agent import BayesianAgent
    from agents.ev_agent import EVAgent
    from agents.random_agent import RandomAgent
    
    if matchup == "bayesian_vs_ev":
        res = _run_pairing("Bayesian vs EV UI", 
            lambda s: BayesianAgent(player_id=0, epsilon=0.05, samples=samples, seed=s, opponent_type="TIGHT", forgetting_factor=0.01),
            lambda s: EVAgent(player_id=1, epsilon=0.05, samples=samples, seed=s),
            hands, seeds, samples)
    elif matchup == "bayesian_vs_random":
        res = _run_pairing("Bayesian vs Random UI", 
            lambda s: BayesianAgent(player_id=0, epsilon=0.05, samples=samples, seed=s, opponent_type="LOOSE", forgetting_factor=0.01),
            lambda s: RandomAgent(player_id=1),
            hands, seeds, samples)
    else:
        res = _run_pairing("EV vs Random UI", 
            lambda s: EVAgent(player_id=0, epsilon=0.05, samples=samples, seed=s),
            lambda s: RandomAgent(player_id=1),
            hands, seeds, samples)
            
    return jsonify(res)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
