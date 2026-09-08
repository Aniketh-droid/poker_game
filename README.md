# Bluff & Bayes

[![Tests](https://github.com/Aniketh-droid/Bayesian_poker_agent/actions/workflows/tests.yml/badge.svg)](https://github.com/Aniketh-droid/Bayesian_poker_agent/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

A playable No-Limit Texas Hold'em web app: sit down at a configurable 2-6 player table against a roster of AI opponents that each play a genuinely different, model-backed style — from a Monte-Carlo EV grinder to a Bayesian opponent-profiler that gets better at reading you the longer you play. Every bot talks trash. Nobody folds the same way twice.

| Pick your table | Live at the felt |
| --- | --- |
| ![Table setup screen](static/screenshots/setup_screen.png) | ![Live poker table with taunts](static/screenshots/game_screen.png) |

## 🎲 Overview

Under the hood this is a from-scratch N-handed (2-6 player) poker engine — full side-pot math, button-relative blinds, multiway all-in run-outs — driving a roster of agents that range from simple rule-based personalities to a Bayesian belief-tracker that maintains an independent opponent model *per seat* at the table. None of the bots are neural-network black boxes: every decision traces back to an inspectable expected-value calculation.

### The Bot Roster

| Bot | Personality | Model | Difficulty |
|---|---|---|---|
| 🃏 Wildcard | No plan, no fear | Random actions (baseline) | Easy |
| 🪨 The Rock | Folds until it doesn't | Static tight rules | Easy |
| 📞 Calling Station | Sees one more card, always | Static loose-passive rules | Medium |
| 🧮 The Mathematician | Pure pot odds, no reads | Monte Carlo EV (multiway-aware) | Medium |
| 🔥 The Maniac | Bets and raises constantly | Static loose-aggressive rules | Hard |
| 🕵️ The Profiler | Learns your tendencies hand by hand | Per-opponent Bayesian belief + empirical-Bayes adaptation | Hard |
| 🤖 The Data Scientist | Trained on simulated hands | Ensemble of the EV + Bayesian models (see below) | Hard |

Every bot is wired through `agents/personalities.py`, a metadata/taunt registry decoupled from actual decision logic — it's purely presentational (avatar, tagline, situational trash talk), so the personality layer and the decision layer can evolve independently.

### About "The Data Scientist"

`agents/data_scientist_agent.py` is a genuine ensemble bot, not a placeholder: it blends the EV agent's pure pot-odds math with the Bayesian agent's opponent-profiling EV, and the blend weight isn't fixed. Early in a match neither sub-model has real signal on the table, so the two are weighted evenly; as the Bayesian half accumulates real observations of the live opponents (the same per-opponent `OpponentStats` "The Profiler" uses to adapt its own read), the ensemble trusts its opponent-aware estimate more, up to a capped ceiling. See `_bayes_confidence()` in that file.

### Key Features
*   **True multiway engine**: side pots, button-relative blinds, and all-in run-outs generalized from a 2-player-only engine, verified with dedicated stress tests (`tests/test_multiway_engine.py`) hammering unequal all-in stacks for zero-sum and no-negative-stack invariants across 2-6 handed tables.
*   **Per-opponent Bayesian modeling**: `BayesianAgent` ("The Profiler") tracks an independent belief distribution and empirical fold/call statistics *for every live opponent*, not one shared model — so it reads a Maniac differently from a Rock, updating each in real time.
*   **A live taunt feed**: every action and every hand result can trigger a personality-appropriate line, shown as a floating speech bubble over the bot's seat and logged in the "Table Talk" panel.
*   **Configurable tables**: 2 to 6 players, pick your opponents from the roster or hit "Deal Me In" to fill empty seats randomly.
*   **Interactive Web App**: a Flask backend with isolated per-session game state, so multiple people can each play their own match concurrently.

---

## 🧠 Core Architecture & Mathematical Flow

1.  **Game Engine (`engine/`)**: `GameState` and `play_hand_multiway()` handle the full rules of N-handed Texas Hold'em — pot/side-pot tracking, board cards, legal actions, all-in run-outs.
2.  **Belief Module (`belief/`)**: When an opponent acts, Bayesian-backed agents use Bayes' Theorem and likelihood tables to update a probability distribution over that opponent's hand "bucket" — tracked per-seat at a multiway table.
3.  **Decision Engine (`decision/`, `evaluation/`)**: Runs Monte Carlo simulations (multiway-aware via `estimate_equity_multiway`) against the current belief(s) to estimate win equity, and computes the Expected Value of folding, calling, or betting (`compute_ev` / `compute_ev_multiway`).
4.  **Web UI (`app.py`, `static/`)**: Runs a persistent multi-hand match per browser session — stacks carry over, the button rotates, and the game continues until you bust, the table busts, or you leave.

---

## 🚀 Getting Started

### Prerequisites
*   Python 3.8+

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/Aniketh-droid/Bayesian_poker_agent.git
   cd Bayesian_poker_agent
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   For running the test suite too, install the dev requirements instead:
   ```bash
   pip install -r requirements-dev.txt
   ```

### Usage

Run the Flask server:
```bash
python app.py
```
*Navigate to `http://localhost:5000` in your browser.* Pick a table size (2-6), choose your opponents from the roster (or let "Deal Me In" fill the rest randomly), and play. Set `FLASK_SECRET_KEY` in your environment for a stable session key across restarts (otherwise a random one is generated each time the server starts).

### Running Tests
```bash
pip install -r requirements-dev.txt
pytest
```
The suite covers the hand evaluator, hand bucketing, the Bayesian belief update, the opponent model, EV calculation (heads-up and multiway), Monte Carlo equity estimation (including multiway), the action space/legality rules, seed reproducibility, street threading through `observe()`, the empirical-Bayes opponent-stats shrinkage, the N-handed engine (side pots, zero-sum invariants, fold-down-to-one, heads-up backward compatibility), and an end-to-end integration test that plays full hands through the real engine. CI runs this suite on every push via GitHub Actions (see the badge above).

### Running with Docker
```bash
docker build -t bayesian-poker-agent .
docker run -p 5000:5000 -e FLASK_SECRET_KEY=$(openssl rand -hex 32) bayesian-poker-agent
```
This is the easiest way to deploy the web UI to a host like Render, Fly.io, or Railway for a live, shareable demo link.

---

## 🐞 Two Real Bugs, Found and Fixed

Early development compared the decision-making agents head-to-head and turned up two real issues, both fixed in code that's still central to how "The Profiler" and "The Data Scientist" play today:

1.  **`observe()` wasn't receiving the actual street.** `engine/game_engine.py` used to call `agents[1 - pid].observe(action)` with no `street` argument, and `BayesianAgent.observe(self, opponent_action, street=0)` silently defaulted to street `0` (preflop) for every call — so every postflop belief update was computed against the *preflop* row of the likelihood tables in `opponent_model.py`, regardless of what street the action actually happened on. **Fixed**: the engine now captures the street *before* `apply_action()` (since a check/call closing the street can advance it as a side effect) and passes it through, with a regression test (`tests/test_observe_street_threading.py`) asserting the engine reports real, non-decreasing streets across a hand instead of always `0`.

2.  **The opponent archetype was a static, unlearned label.** Each bot's `opponent_type` (TIGHT/LOOSE/AGGRESSIVE) was fixed at construction and never adapted, no matter how much real behavior the agent observed. **Fix**: `belief/opponent_stats.py` adds an `OpponentStats` tracker that records the opponent's real fold vs. call/check responses per street across a match. `decision/ev_calculator.compute_ev()`'s bet-EV branch blends the static archetype-table prior with these empirical per-street rates via empirical-Bayes shrinkage (`blend_with_prior()`, prior worth 10 pseudo-observations): with zero real observations it's numerically identical to the old static-only behavior, and as more hands are observed the estimate converges toward the opponent's true frequency. The honest caveat on scope: this corrects one scalar pair (fold/call rate) per street via shrinkage — it doesn't touch bet-sizing frequency, the hand-bucket likelihood tables themselves, or give the agent a genuinely *learned* representation of its opponent.

**Multiway simplification, disclosed rather than hidden**: at a 3-6 handed table, `compute_ev_multiway()` computes "does everyone fold" as the *product* of each live opponent's individual fold probability — a deliberate simplification, not a full N-player game-theoretic solve (a real multiway solve needs CFR-style search over every opponent's response). It captures the right qualitative shape (more live opponents → harder to bluff everyone off a hand) without needing a full solver in a real-time bot's hot path — the right tradeoff for a fun-first game, not a research claim of multiway optimality.

</details>

## 🔮 Future Improvements

*   **Learned ensemble weighting for The Data Scientist**: replace the fixed confidence floor/ceiling in `_bayes_confidence()` with a weight learned from self-play data instead of hand-tuned constants.
*   **Dynamic RL Opponent Modeling**: go further than the existing empirical-Bayes fold/call correction — replace the hardcoded bet-sizing and hand-bucket likelihood tables with an online RL agent that learns an opponent's full playstyle over time.
*   **Deep RL for Multi-Street Planning**: `ev_calculator.py` currently uses a greedy, one-step EV algorithm; PPO-style training could let an agent learn multi-street bluff lines.
*   **Real human-vs-human tables**: the current build is human-vs-bots; networked human-vs-human seats at the same table is a natural next phase.
*   **Unsupervised hand bucketing**: cluster hole cards by mathematical equity (e.g. K-Means) instead of relying on static heuristic bucket definitions.

---

## 🤝 Contributing
Contributions, issues, and feature requests are welcome! Feel free to check the issues page.

## 📝 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
