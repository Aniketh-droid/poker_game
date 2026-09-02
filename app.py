import logging
import os
import secrets
import threading
import uuid

from flask import Flask, jsonify, request, send_from_directory, session

from agents.web_human_agent import WebHumanAgent
from agents.ev_agent import EVAgent
from agents.random_agent import RandomAgent
from agents.bayesian_agent import BayesianAgent
from engine.game_engine import play_hand

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', static_url_path='')

# A session cookie needs a secret key to be signed. In production, set
# FLASK_SECRET_KEY so sessions survive process restarts / multiple workers;
# otherwise we generate a random per-process key (fine for a single-process
# local demo, but every restart invalidates existing player sessions).
_secret_key = os.environ.get("FLASK_SECRET_KEY")
if not _secret_key:
    _secret_key = secrets.token_hex(32)
    logger.warning(
        "FLASK_SECRET_KEY not set - using an ephemeral per-process secret key. "
        "Set FLASK_SECRET_KEY in the environment for a stable, production-safe key."
    )
app.secret_key = _secret_key

# Per-session game state, keyed by a random session id stored in the user's
# signed session cookie. This replaces a single global dict so that
# concurrent players don't overwrite each other's in-progress hand.
games: dict = {}
action_events: dict = {}
engine_threads: dict = {}
_state_lock = threading.Lock()


def _default_state() -> dict:
    return {
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
        "villain_thoughts": [],
    }


def _get_session_id() -> str:
    sid = session.get("sid")
    if not sid:
        sid = uuid.uuid4().hex
        session["sid"] = sid
    return sid


def run_engine_thread(opponent_type: str, sid: str) -> None:
    state = games[sid]
    action_event = action_events[sid]
    hero = WebHumanAgent(player_id=0, shared_state=state, action_event=action_event)

    if opponent_type == 'RANDOM':
        villain = RandomAgent(player_id=1)
    elif opponent_type == 'EV':
        villain = EVAgent(player_id=1, epsilon=0.0, samples=50)
    else:  # BAYESIAN
        villain = BayesianAgent(player_id=1, opponent_type="TIGHT", samples=50)

    # Wrap the villain's act method to capture their thought process
    original_act = villain.act
    def wrapped_act(game_state):
        action = original_act(game_state)
        thought = f"Chose <strong>{action}</strong>."
        if hasattr(villain, '_last_ev_dict'):
            # clean up ev dict for display
            evs = " | ".join([f"{a}: {ev:.2f}" for a, ev in villain._last_ev_dict.items()])
            thought += f" <br><span style='color: #64748b; font-size: 0.85em'>Expected Values: [{evs}]</span>"
        if hasattr(villain, '_last_entropy'):
            thought += f" <br><span style='color: #ea580c; font-size: 0.85em'>Uncertainty (Entropy): {villain._last_entropy:.2f}</span>"

        state.setdefault("villain_thoughts", []).append(f"<b>Street {game_state.street}</b>: {thought}")
        return action
    villain.act = wrapped_act

    try:
        from evaluation.hand_evaluator import compare as compare_hands
        evaluator = type("Eval", (), {"compare": staticmethod(compare_hands)})()
        result = play_hand(hero, villain, evaluator=evaluator, return_details=True)

        # Once hand is over
        state["game_over"] = True
        state["waiting_for_human"] = False

        # Map tuples like (14, 0) to standard string for frontend if array
        if result and "private_cards" in result:
            state["villain_cards"] = [str(c) for c in result["private_cards"][1]]
            state["board"] = [str(c) for c in result["board"]]

        state["last_result"] = {
            "outcome": result["outcome"],
            "chip_delta": result["chip_delta"],
        }

    except Exception:
        logger.exception("Engine thread failed for session %s (opponent=%s)", sid, opponent_type)
        state["game_over"] = True
        state["waiting_for_human"] = False


@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/api/start', methods=['POST'])
def start_game():
    sid = _get_session_id()
    body = request.get_json(silent=True) or {}
    opponent = body.get("opponent", "BAYESIAN")

    with _state_lock:
        games[sid] = _default_state()
        action_events[sid] = threading.Event()

    thread = threading.Thread(target=run_engine_thread, args=(opponent, sid), daemon=True)
    engine_threads[sid] = thread
    thread.start()
    return jsonify({"status": "started"})


@app.route('/api/state', methods=['GET'])
def get_state():
    sid = _get_session_id()
    return jsonify(games.get(sid, _default_state()))


@app.route('/api/action', methods=['POST'])
def handle_action():
    sid = _get_session_id()
    state = games.get(sid)
    if state is None or not state.get("waiting_for_human"):
        return jsonify({"error": "Not waiting for action"}), 400

    body = request.get_json(silent=True) or {}
    action = body.get("action")
    if action not in state.get("legal_actions", []):
        return jsonify({"error": "Invalid action"}), 400

    state["human_action"] = action
    event = action_events.get(sid)
    if event is not None:
        event.set()
    return jsonify({"status": "ok"})


@app.route('/api/simulate', methods=['POST'])
def run_simulation():
    body = request.get_json(silent=True) or {}
    matchup = body.get("matchup", "bayesian_vs_ev")
    try:
        hands = int(body.get("hands", 100))
    except (TypeError, ValueError):
        return jsonify({"error": "hands must be an integer"}), 400
    hands = max(1, min(hands, 5000))  # guard against absurd/blocking request sizes
    seeds = [12345]  # keeping it fast for web ui
    samples = 25

    from main import _run_pairing
    from agents.bayesian_agent import BayesianAgent
    from agents.ev_agent import EVAgent
    from agents.random_agent import RandomAgent

    try:
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
    except Exception:
        logger.exception("Simulation failed for matchup=%s hands=%s", matchup, hands)
        return jsonify({"error": "Simulation failed"}), 500

    return jsonify(res)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
