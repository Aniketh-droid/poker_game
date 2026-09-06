import logging
import os
import random
import secrets
import threading
import time
import uuid

from flask import Flask, jsonify, request, send_from_directory, session

from agents.web_human_agent import WebHumanAgent
from agents.ev_agent import EVAgent
from agents.random_agent import RandomAgent
from agents.tight_agent import TightAgent
from agents.bayesian_agent import BayesianAgent
from agents.maniac_agent import ManiacAgent
from agents.calling_station_agent import CallingStationAgent
from agents.data_scientist_agent import DataScientistAgent
from agents.personalities import PERSONALITIES, list_personalities, get_taunt
from engine.action_space import BB, FOLD, CHECK, CALL, BET_25, BET_50, BET_100, ALL_IN
from engine.game_engine import play_hand_multiway

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
next_hand_events: dict = {}
engine_threads: dict = {}
_state_lock = threading.Lock()

MIN_PLAYERS = 2
MAX_PLAYERS = 6
STARTING_STACK = 50.0 * BB

# Pacing for bot turns, so a human can actually follow the hand instead of
# watching several bots act between one poll and the next. Only applied to
# bots (seat != 0) -- the human's own turn is already paced by them deciding.
ACTION_REVEAL_DELAY = 1.1   # pause after a bot's action lands, before it's applied
TAUNT_FOLLOWUP_DELAY = 0.7  # further pause after a delayed taunt appears


def _default_state() -> dict:
    return {
        "waiting_for_human": False,
        "human_action": None,
        "street": 0,
        "pot": 0,
        "board": [],
        "hero_cards": [],
        "players": [],
        "legal_actions": [],
        "to_call": 0.0,
        "button": 0,
        "hand_number": 0,
        "hand_over": False,
        "game_over": False,
        "game_over_reason": None,
        "last_result": None,
        "action_log": [],
        "seat_meta": [],
        "num_players": 0,
        "stacks": [],
        "stop_requested": False,
    }


def _get_session_id() -> str:
    sid = session.get("sid")
    if not sid:
        sid = uuid.uuid4().hex
        session["sid"] = sid
    return sid


def build_bot(personality_key: str, player_id: int, seed: int):
    """Instantiate the agent behind a personality slug. Falls back to Wildcard
    (RandomAgent) for an unrecognized key rather than raising, since this only
    ever gets called with either a UI-supplied or server-generated key."""
    entry = PERSONALITIES.get(personality_key) or PERSONALITIES["wildcard"]
    cls_name = entry["agent_class"]

    if cls_name == "TightAgent":
        return TightAgent(player_id=player_id)
    if cls_name == "EVAgent":
        # Sample count is deliberately much lower than the academic benchmark's
        # (200): this bot needs to decide in well under a second at a 6-handed
        # table, not produce a publishable equity estimate. 70 samples is
        # still enough to separate "clearly ahead" from "clearly behind" for a
        # fun table, per manual timing checks against the 6-handed stress test.
        return EVAgent(player_id=player_id, epsilon=0.04, samples=70, seed=seed)
    if cls_name == "BayesianAgent":
        # "The Profiler" leans TIGHT-prior (reads opponents as cautious until
        # proven otherwise); any other Bayesian-backed slot defaults LOOSE.
        opp_type = "TIGHT" if personality_key == "the-profiler" else "LOOSE"
        return BayesianAgent(
            player_id=player_id, epsilon=0.05, samples=70, seed=seed,
            opponent_type=opp_type, forgetting_factor=0.02,
        )
    if cls_name == "ManiacAgent":
        return ManiacAgent(player_id=player_id, seed=seed, aggression=0.75)
    if cls_name == "CallingStationAgent":
        return CallingStationAgent(player_id=player_id, seed=seed, fold_chance=0.03)
    if cls_name == "DataScientistAgent":
        # Runs an EVAgent AND a BayesianAgent internally every decision (see
        # agents/data_scientist_agent.py) -- double the per-model work of the
        # other two, so its sub-model sample count is trimmed further.
        return DataScientistAgent(player_id=player_id, seed=seed, epsilon=0.04, samples=55)
    # RandomAgent / unknown -> Wildcard
    return RandomAgent(player_id=player_id, rng=random.Random(seed))


def _trigger_for_action(action: str, to_call_before: float) -> str:
    if action == FOLD:
        return "fold"
    if action == CHECK:
        return "check"
    if action == CALL:
        return "call"
    if action in (BET_25, BET_50, BET_100, ALL_IN):
        return "bet" if to_call_before <= 1e-9 else "raise"
    return "idle"


def _publish_table_snapshot(state: dict, game_state, seat_meta: list) -> None:
    """Refresh the live table view (stacks, current bets, folded/all-in status,
    board, pot, whose turn it is) from game_state. Called right before EVERY
    seat's act() -- bots included -- not just the human's, so a poll landing
    mid-hand (while several bots act in a row between human turns) still shows
    an up-to-date table instead of a snapshot frozen at the human's last turn."""
    n = len(game_state.stacks)
    folded = getattr(game_state, "folded", set())
    all_in = getattr(game_state, "all_in", set())
    street_bets = getattr(game_state, "street_bets", [0.0] * n)
    button = getattr(game_state, "button", 0)
    # Same button-relative blind formula play_hand_multiway() uses to actually
    # post blinds -- computed here too so the UI can label SB/BB seats and make
    # the turn order (blinds -> first-to-act -> clockwise) visually obvious,
    # rather than the human having to infer it from chip amounts alone.
    if n == 2:
        sb_seat, bb_seat = button % n, (button + 1) % n
    else:
        sb_seat, bb_seat = (button + 1) % n, (button + 2) % n
    players = []
    for i in range(n):
        meta = seat_meta[i] if i < len(seat_meta) else {}
        players.append({
            "seat": i, "is_hero": i == 0,
            "key": meta.get("key"), "name": meta.get("name"), "avatar": meta.get("avatar"),
            "stack": game_state.stacks[i],
            "street_bet": street_bets[i] if i < len(street_bets) else 0.0,
            "folded": i in folded, "all_in": i in all_in,
            "is_sb": i == sb_seat, "is_bb": i == bb_seat,
        })
    with _state_lock:
        state["players"] = players
        state["board"] = [str(c) for c in game_state.board]
        state["pot"] = game_state.pot
        state["street"] = game_state.street
        state["button"] = getattr(game_state, "button", state.get("button", 0))
        state["current_seat"] = getattr(game_state, "current_player", None)
        state["to_call"] = getattr(game_state, "to_call", 0.0)


def _log_event(state: dict, entry: dict) -> None:
    with _state_lock:
        log = state.setdefault("action_log", [])
        log.append(entry)
        if len(log) > 200:
            del log[: len(log) - 200]


def run_match_thread(sid: str, num_players: int, bot_keys: list) -> None:
    """Play hands back-to-back (stacks carrying over, button rotating) until the
    human busts, every bot busts, or the player leaves the table. Pauses after
    each hand and waits for a /api/next_hand click so the UI can show the
    showdown/result before dealing again."""
    state = games[sid]
    action_event = action_events[sid]
    next_hand_event = next_hand_events[sid]

    seat_meta = [{"key": "human", "name": "You", "avatar": "\U0001F9D1"}]
    for k in bot_keys:
        entry = PERSONALITIES.get(k) or PERSONALITIES["wildcard"]
        seat_meta.append({"key": k, "name": entry["name"], "avatar": entry["avatar"]})

    hero = WebHumanAgent(player_id=0, shared_state=state, action_event=action_event, seat_meta=seat_meta)
    base_seed = random.randint(0, 10 ** 6)
    bots = [build_bot(k, i + 1, seed=base_seed + i * 977) for i, k in enumerate(bot_keys)]
    agents = [hero] + bots

    def _wrap(agent_obj, seat_idx):
        original_act = agent_obj.act
        is_hero = (seat_idx == 0)

        def wrapped(game_state):
            to_call_before = getattr(game_state, "to_call", 0.0)
            _publish_table_snapshot(state, game_state, seat_meta)
            action = original_act(game_state)
            meta = seat_meta[seat_idx]
            trigger = _trigger_for_action(action, to_call_before)
            street = game_state.street

            # 1) Announce the action itself first -- "The Rock raises to $10"
            #    lands on its own, with no taunt attached yet.
            _log_event(state, {
                "seat": seat_idx, "name": meta["name"], "avatar": meta["avatar"],
                "action": action, "street": street, "trigger": trigger, "taunt": "",
            })

            if is_hero:
                # The human's own turn is already paced by them deciding --
                # no artificial delay, and humans have no taunts to reveal.
                return action

            # 2) Give the human a moment to actually see that action land
            #    before the next seat's turn starts. Without this, several
            #    bots played out a whole betting round between one poll and
            #    the next, and it looked like nothing was happening in order.
            time.sleep(ACTION_REVEAL_DELAY)

            # 3) THEN reveal the taunt as its own follow-up beat, if this
            #    personality has one for what it just did.
            taunt = get_taunt(meta["key"], trigger, rng=random.Random(base_seed + seat_idx + hash(action) % 997))
            if taunt:
                _log_event(state, {
                    "seat": seat_idx, "name": meta["name"], "avatar": meta["avatar"],
                    "action": None, "street": street, "trigger": trigger, "taunt": taunt,
                })
                time.sleep(TAUNT_FOLLOWUP_DELAY)

            return action
        agent_obj.act = wrapped

    for i, a in enumerate(agents):
        _wrap(a, i)

    from evaluation.hand_evaluator import compare as compare_hands
    evaluator = type("Eval", (), {"compare": staticmethod(compare_hands)})()

    stacks = [STARTING_STACK] * num_players
    button = 0
    hand_number = 0

    with _state_lock:
        state["seat_meta"] = seat_meta
        state["num_players"] = num_players
        state["stacks"] = list(stacks)
        state["game_over"] = False

    try:
        while True:
            if state.get("stop_requested"):
                break

            hand_number += 1
            state["hand_number"] = hand_number
            state["hand_over"] = False
            state["last_result"] = None

            result = play_hand_multiway(
                agents, seed=base_seed + hand_number * 7919, evaluator=evaluator,
                button=button % num_players, stacks=list(stacks), return_details=True,
            )
            stacks = [stacks[i] + result["chip_delta"][i] for i in range(num_players)]
            button = (button + 1) % num_players

            folded_ids = set(result.get("folded_ids", []))
            reveals = {
                str(i): [str(c) for c in result["private_cards"][i]]
                for i in range(num_players) if i not in folded_ids
            }

            for i in range(1, num_players):
                if i in folded_ids:
                    continue
                meta = seat_meta[i]
                trig = "win" if i in result["winner_ids"] else "lose"
                t = get_taunt(meta["key"], trig, rng=random.Random(base_seed + hand_number + i))
                if t:
                    _log_event(state, {
                        "seat": i, "name": meta["name"], "avatar": meta["avatar"],
                        "action": None, "street": 4, "trigger": trig, "taunt": t,
                    })
                    time.sleep(0.5)  # let each reaction land on its own beat

            with _state_lock:
                state["stacks"] = list(stacks)
                state["button"] = button
                state["last_result"] = {
                    "outcome": result["outcome"],
                    "winner_ids": result["winner_ids"],
                    "winner_names": [seat_meta[i]["name"] for i in result["winner_ids"]],
                    "chip_delta": result["chip_delta"],
                    "board": [str(c) for c in result["board"]],
                    "reveals": reveals,
                    "hand_number": hand_number,
                    "stacks": list(stacks),
                }
                state["hand_over"] = True
                state["waiting_for_human"] = False

            alive_human = stacks[0] > 1e-9
            alive_bots = sum(1 for s in stacks[1:] if s > 1e-9)
            if not alive_human:
                state["game_over"] = True
                state["game_over_reason"] = "human_busted"
                break
            if alive_bots == 0:
                state["game_over"] = True
                state["game_over_reason"] = "human_wins"
                break

            next_hand_event.clear()
            next_hand_event.wait(timeout=600)  # safety valve if the tab is abandoned mid-session
            if state.get("stop_requested"):
                break
    except Exception:
        logger.exception("Match thread failed for session %s", sid)
        state["game_over"] = True
        state["game_over_reason"] = "error"
        state["waiting_for_human"] = False


@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/api/personalities', methods=['GET'])
def get_personalities():
    return jsonify(list_personalities())


@app.route('/api/start', methods=['POST'])
def start_game():
    sid = _get_session_id()
    body = request.get_json(silent=True) or {}

    try:
        num_players = int(body.get("num_players", 4))
    except (TypeError, ValueError):
        return jsonify({"error": "num_players must be an integer"}), 400
    num_players = max(MIN_PLAYERS, min(MAX_PLAYERS, num_players))

    valid_keys = set(PERSONALITIES.keys())
    bot_keys = body.get("bots")
    needed = num_players - 1
    if not isinstance(bot_keys, list) or len(bot_keys) != needed or not all(k in valid_keys for k in bot_keys):
        pool = list(PERSONALITIES.keys())
        random.shuffle(pool)
        bot_keys = (pool * ((needed // len(pool)) + 1))[:needed]

    with _state_lock:
        games[sid] = _default_state()
        action_events[sid] = threading.Event()
        next_hand_events[sid] = threading.Event()

    thread = threading.Thread(target=run_match_thread, args=(sid, num_players, bot_keys), daemon=True)
    engine_threads[sid] = thread
    thread.start()
    return jsonify({"status": "started", "num_players": num_players, "bots": bot_keys})


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


@app.route('/api/next_hand', methods=['POST'])
def next_hand():
    sid = _get_session_id()
    state = games.get(sid)
    if state is None or not state.get("hand_over") or state.get("game_over"):
        return jsonify({"error": "Not ready for the next hand"}), 400

    event = next_hand_events.get(sid)
    if event is not None:
        event.set()
    return jsonify({"status": "ok"})


@app.route('/api/leave', methods=['POST'])
def leave_game():
    sid = _get_session_id()
    state = games.get(sid)
    if state is not None:
        state["stop_requested"] = True
        ev = action_events.get(sid)
        if ev is not None:
            ev.set()
        nh = next_hand_events.get(sid)
        if nh is not None:
            nh.set()
    return jsonify({"status": "ok"})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
