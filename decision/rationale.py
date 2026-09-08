"""
Post-hand decision rationale: turns each agent's already-computed internal
decision state (EV dicts, hand-strength buckets, belief entropy, fire
probabilities) into a plain-English explanation of why it chose the action
it chose -- grounded in its actual hole cards, the board, and what already
happened this street, not just an abstract strategy description.

WHY THIS EXISTS: the user wants to be able to explain this project to
interviewers -- not just "there are 7 bot personalities" but "here's why The
Profiler check-raised on that river, holding 9s 9c on a Ks 9d 4h board, after
the Maniac bet into it." Every number surfaced here is read directly off the
agent's own private decision-time state (the same EV dict, belief, or hand
bucket the agent used to actually choose the action) -- this module never
recomputes or invents anything, it only formats what already happened,
including the real cards, into English.

HIDDEN-INFORMATION NOTE: app.py deliberately only reveals this per hand once
that hand is over (see run_match_thread's hand_ctx), never live -- a bot's
hole cards, EV dict, or belief read all imply its hand strength, so showing
this mid-hand would let a human opponent read bots' hands off this panel
instead of playing the game. This module itself is agnostic to when it's
called; the hiding is entirely app.py's responsibility.
"""

from typing import Any, Dict, List, Optional

from engine.action_space import FOLD, CHECK, CALL, BET_25, BET_50, BET_100, ALL_IN

_ACTION_WORDS = {
    FOLD: "fold",
    CHECK: "check",
    CALL: "call",
    BET_25: "bet 25% of the pot",
    BET_50: "bet half the pot",
    BET_100: "bet the full pot",
    ALL_IN: "go all-in",
}

# Third-person past-tense form of the same actions, for narrating what other
# seats already did this street (see _context_phrase).
_ACTION_NARRATION = {
    FOLD: "folded",
    CHECK: "checked",
    CALL: "called",
    BET_25: "bet 25% of the pot",
    BET_50: "bet half the pot",
    BET_100: "bet the full pot",
    ALL_IN: "went all-in",
}

_BET_ACTIONS = (BET_25, BET_50, BET_100, ALL_IN)

# rank/suit -> display string, matching static/app.js's RANKS/SUITS tables
# exactly (same suit-index convention engine/cards.py's (rank, suit) tuples
# use) so a bot's cards read here the same way they'd render on the felt.
_RANKS = {14: "A", 13: "K", 12: "Q", 11: "J", 10: "T"}
_SUITS = ["♥", "♦", "♠", "♣"]  # hearts, diamonds, spades, clubs

_STREET_LABELS = {0: "preflop", 1: "the flop", 2: "the turn", 3: "the river"}

# What each rule-based agent's own stated strategy does with a given hand
# bucket -- lifted from the comments/branches in tight_agent.py, matched to
# the closest analogous postflop bucket for the other two rule-based bots.
_TIGHT_PLAYBOOK = {
    "PREMIUM": "bet big for value",
    "STRONG": "call to keep the pot controlled rather than raise",
    "MEDIUM": "check it down rather than build the pot",
    "SPECULATIVE": "get out cheaply unless it's free to continue",
    "TRASH": "get out cheaply unless it's free to continue",
    "STRONG_MADE": "bet big for value",
    "MEDIUM_MADE": "call to keep the pot controlled rather than raise",
    "WEAK_MADE": "check it down rather than build the pot",
    "STRONG_DRAW": "check it down rather than build the pot",
    "WEAK_DRAW": "get out cheaply unless it's free to continue",
    "AIR": "get out cheaply unless it's free to continue",
}


def _card_str(card: Any) -> str:
    try:
        rank, suit = card
    except (TypeError, ValueError):
        return str(card)
    r = _RANKS.get(rank, str(rank))
    s = _SUITS[suit] if isinstance(suit, int) and 0 <= suit < len(_SUITS) else "?"
    return f"{r}{s}"


def _cards_str(cards: Optional[List[Any]]) -> str:
    return " ".join(_card_str(c) for c in cards) if cards else ""


def _hand_phrase(hole_cards: Optional[List[Any]], board: Optional[List[Any]]) -> str:
    """'Holding As Kd on a board of Qs 7d 2c' / 'Holding As Kd preflop'."""
    if not hole_cards:
        return ""
    holding = f"Holding {_cards_str(hole_cards)}"
    return f"{holding} on a board of {_cards_str(board)}" if board else f"{holding} preflop"


def _context_phrase(prior_actions: Optional[List[Dict[str, Any]]], street: int) -> str:
    """'After The Maniac bet half the pot and Calling Station called' -- the
    real actions already taken by other seats on this street, in order, or ''
    if this bot was first to act. Built entirely from app.py's real action
    log for the hand, never invented."""
    if not prior_actions:
        return ""
    same_street = [a for a in prior_actions if a.get("street") == street]
    if not same_street:
        return ""
    bits = [f"{a['name']} {_ACTION_NARRATION.get(a['action'], a['action'])}" for a in same_street]
    if len(bits) == 1:
        joined = bits[0]
    elif len(bits) == 2:
        joined = f"{bits[0]} and {bits[1]}"
    else:
        joined = ", ".join(bits[:-1]) + f", and {bits[-1]}"
    return f"After {joined}"


def _lead_in(hole_cards: Optional[List[Any]], board: Optional[List[Any]],
             prior_actions: Optional[List[Dict[str, Any]]], street: int) -> str:
    """The 1-2 sentence factual setup shared by every agent type: what it was
    holding, and what already happened this street. Empty string if no
    game_state was supplied (keeps this module usable without one)."""
    sentences = []
    hp = _hand_phrase(hole_cards, board)
    if hp:
        sentences.append(hp + ".")
    ctx = _context_phrase(prior_actions, street)
    if ctx:
        sentences.append(ctx + ".")
    return (" ".join(sentences) + " ") if sentences else ""


def _ev_table_str(ev_dict: Dict[str, float], legal: Optional[List[str]]) -> str:
    if not ev_dict:
        return ""
    actions = legal if legal else list(ev_dict.keys())
    ranked = sorted((a for a in actions if a in ev_dict), key=lambda a: -ev_dict[a])
    return ", ".join(f"{_ACTION_WORDS.get(a, a)} = {ev_dict[a]:+.2f}" for a in ranked)


def _base_entry(seat_idx: int, strategy_type: str, summary: str, **extra: Any) -> Dict[str, Any]:
    entry = {"seat": seat_idx, "strategy_type": strategy_type, "summary": summary}
    entry.update(extra)
    return entry


def explain_decision(
    agent_obj: Any,
    action: str,
    legal: Optional[List[str]],
    seat_idx: int,
    game_state: Any = None,
    prior_actions: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Build one rationale entry for the action `agent_obj` just chose.
    `legal` is the action list the agent actually saw (so the EV comparison
    shown reflects only what was really on the table). `game_state`, if
    given, is the live decision-time state -- read-only here, for this
    seat's actual hole cards and the board so far. `prior_actions` is the
    real action log for this hand so far (app.py's hand_ctx["actions"]),
    used to narrate what other seats already did this street."""
    cls = type(agent_obj).__name__
    action_word = _ACTION_WORDS.get(action, action)

    hole_cards = None
    board: List[Any] = []
    street = 0
    if game_state is not None:
        hole_cards = getattr(game_state, "private_cards", {}).get(seat_idx)
        board = getattr(game_state, "board", []) or []
        street = getattr(game_state, "street", 0)
    lead = _lead_in(hole_cards, board, prior_actions, street)

    if cls in ("EVAgent", "BayesianAgent", "DataScientistAgent"):
        ev_dict = getattr(agent_obj, "_last_ev_dict", None) or {}
        best_action = max(ev_dict, key=ev_dict.get) if ev_dict else None
        explored = bool(ev_dict) and best_action is not None and best_action != action
        ev_table = _ev_table_str(ev_dict, legal)

        if cls == "EVAgent":
            n_opp = getattr(agent_obj, "_last_num_opponents", None)
            opp_phrase = f"{n_opp} live opponent{'s' if n_opp != 1 else ''}" if n_opp is not None else "its live opponents"
            summary = f"{lead}It ran a Monte Carlo equity simulation against {opp_phrase} and compared expected value across every legal action ({ev_table})."
            if explored:
                summary += f" {action_word.capitalize()} wasn't the highest-EV option -- this was an exploration (epsilon-greedy) turn rather than a pure best-response."
            else:
                summary += f" {action_word.capitalize()} had the highest expected value, so that's what it played."
            return _base_entry(seat_idx, "monte-carlo-ev", summary, ev_table=ev_dict)

        if cls == "BayesianAgent":
            entropy = getattr(agent_obj, "_last_entropy", None)
            beliefs = getattr(agent_obj, "_beliefs", None) or {}
            reads = []
            for opp, belief in beliefs.items():
                if not belief:
                    continue
                top_bucket = max(belief, key=belief.get)
                reads.append(f"seat {opp} likely {top_bucket} ({belief[top_bucket] * 100:.0f}%)")
            reads_str = "; ".join(reads) if reads else "no confident reads yet"
            summary = f"{lead}Belief on opponents: {reads_str}. Compared expected value across every legal action using those beliefs ({ev_table})."
            if entropy is not None:
                summary += f" Belief entropy was {entropy:.2f} (lower means more confident), which scaled down how often it explores/bluffs this turn."
            if explored:
                summary += f" {action_word.capitalize()} wasn't the top-EV play -- an exploration turn."
            else:
                summary += f" {action_word.capitalize()} was the highest-EV action given those reads."
            return _base_entry(seat_idx, "bayesian-ev", summary, ev_table=ev_dict, entropy=entropy)

        # DataScientistAgent: a confidence-weighted ensemble blend of an
        # EVAgent and a BayesianAgent sub-model (see agents/data_scientist_agent.py
        # -- weight shifts toward the Bayesian read as it observes the live
        # opponents more, instead of a flat 50/50 average).
        bayes_weight = getattr(agent_obj, "_last_bayes_weight", 0.5)
        ev_weight = 1.0 - bayes_weight
        summary = (
            f"{lead}Blended two internal models -- a pure Monte Carlo equity model (weight {ev_weight * 100:.0f}%) "
            f"and a belief-tracking Bayesian model (weight {bayes_weight * 100:.0f}%, higher the more it's observed "
            f"these opponents) -- into one expected-value estimate per action ({ev_table}). "
            f"{action_word.capitalize()} had the best blended EV."
        )
        return _base_entry(seat_idx, "ensemble-ev", summary, ev_table=ev_dict, bayes_weight=bayes_weight)

    if cls == "TightAgent":
        bucket = getattr(agent_obj, "_last_bucket", None)
        playbook = _TIGHT_PLAYBOOK.get(bucket, "play straightforwardly")
        summary = (
            f"{lead}Classified this hand as {bucket or 'unclassified'} using deterministic hand-bucket rules "
            f"(no Monte Carlo, no opponent modeling). Its fixed playbook for that bucket is to {playbook}, "
            f"which is why it chose to {action_word}."
        )
        return _base_entry(seat_idx, "rule-based-tight", summary, bucket=bucket)

    if cls == "ManiacAgent":
        bucket = getattr(agent_obj, "_last_bucket", None)
        fire_prob = getattr(agent_obj, "_last_fire_prob", None)
        fired = action in _BET_ACTIONS
        if fire_prob is not None:
            summary = (
                f"{lead}Classified this hand as {bucket or 'unclassified'}, then weighed a {fire_prob * 100:.0f}% "
                f"probability of firing a bet/raise regardless of hand strength (aggression is deliberately "
                f"only weakly tied to hand quality for this personality). That roll came up "
                f"{'aggressive' if fired else 'passive'}, landing on {action_word}."
            )
        else:
            summary = f"{lead}Chose to {action_word} based on its high, largely hand-strength-independent aggression setting."
        return _base_entry(seat_idx, "rule-based-aggressive", summary, bucket=bucket, fire_probability=fire_prob)

    if cls == "CallingStationAgent":
        bucket = getattr(agent_obj, "_last_bucket", None)
        summary = (
            f"{lead}Classified this hand as {bucket or 'unclassified'}, but its whole strategy is to almost never "
            f"fold or raise regardless of hand strength -- it just calls -- which is why it chose to {action_word}."
        )
        return _base_entry(seat_idx, "rule-based-passive", summary, bucket=bucket)

    if cls == "RandomAgent":
        summary = f"{lead}Wildcard runs no strategy at all -- {action_word} was picked uniformly at random from its legal actions."
        return _base_entry(seat_idx, "random", summary)

    # WebHumanAgent (the human player) or anything unrecognized: no AI
    # rationale to give. Callers should generally skip logging this for the
    # human seat rather than surface a trivial entry.
    return _base_entry(seat_idx, "human", f"You chose to {action_word}.")
