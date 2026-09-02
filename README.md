# Bayesian Poker Agent

[![Tests](https://github.com/Aniketh-droid/Bayesian_poker_agent/actions/workflows/tests.yml/badge.svg)](https://github.com/Aniketh-droid/Bayesian_poker_agent/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

A high-performance, Bayesian-inference-based poker agent for heads-up No-Limit Texas Hold'em. This project features a robust Python engine, a probabilistic decision-making AI, and a premium "glass-box" web interface that allows users to play against the AI while observing its real-time mathematical thought process.

| Live table | Glass-box reasoning, revealed at showdown |
| --- | --- |
| ![Poker table UI](static/screenshots/web_ui_table.png) | ![AI reasoning panel](static/screenshots/web_ui_glass_box.png) |

## 🎲 Overview
Unlike traditional poker AIs that rely on computationally expensive Counterfactual Regret Minimization (CFR) and massive game trees, this agent uses **Bayesian Inference combined with Hand Bucketing**. 

This reduces the millions of possible poker states into a lightweight, easily computable probability problem that runs instantly. The agent calculates the **Expected Value (EV)** of every possible action dynamically, adjusting its strategy based on its calculated belief about the opponent's hidden cards.

### Key Features
*   **Bayesian "Glass Box" AI**: No neural network black-boxes here. The AI explicitly calculates probabilities across human-readable hand buckets (e.g., "Premium", "Air", "Strong Draw"), and the web UI reveals its full EV breakdown and belief entropy for every decision after each hand.
*   **Interactive Web App**: A Flask-based web interface for playing against the agents or visualizing massive AI vs. AI simulations directly in the browser. Each visitor gets isolated, per-session game state, so multiple people can play concurrently.
*   **Entropy-Gated Exploration**: The agent uses Shannon Entropy to measure its own uncertainty. It bluffs and explores when uncertain (high entropy), and plays pure EV poker when confident (low entropy).
*   **Highly Extensible**: Modular design makes it simple to plug in new opponent profiles, reinforcement learning algorithms, or hand evaluation techniques.

---

## 🧠 Core Architecture & Mathematical Flow

The project operates through a complete sense-think-act pipeline:

1.  **Game Engine (`engine/`)**: Handles the rigorous rules of Texas Hold'em, tracking pot sizes, board cards, and legal actions.
2.  **Belief Module (`belief/`)**: When the opponent acts, the AI uses Bayes' Theorem and hardcoded likelihood tables to update its probability distribution over what hand "bucket" the opponent holds.
3.  **Decision Engine (`decision/`, `evaluation/`)**: Runs thousands of Monte Carlo simulations against the current belief distribution to estimate win equity. It mathematically calculates the absolute Expected Value (EV) for folding, calling, or betting.
4.  **Web UI (`app.py`, `static/`)**: Visually renders the AI's internal thought process to the user, acting as a powerful educational tool for poker math.

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

**1. Play Against the AI (Web UI)**
Run the Flask server to open the interactive frontend:
```bash
python app.py
```
*Navigate to `http://localhost:5000` in your browser.* Set `FLASK_SECRET_KEY` in your environment for a stable session key across restarts (otherwise a random one is generated each time the server starts).

**2. Play Against the AI (Terminal)**
Prefer the command line? `play_human.py` runs the same agents in a plain-text REPL:
```bash
python play_human.py
```

**3. Run Headless Simulations**
To run massive AI vs AI multi-seed experiments and print statistical summaries (Mean Chip Gain, Confidence Intervals):
```bash
python main.py
```
Every parameter is configurable via CLI flags instead of editing the script:
```bash
python main.py --hands 5000 --samples 100 --seeds 1 2 3 --matchups bayesian_vs_ev bayesian_vs_random
```
Run `python main.py --help` for the full list.

### Running Tests
```bash
pip install -r requirements-dev.txt
pytest
```
The suite covers the hand evaluator, hand bucketing, the Bayesian belief update, the opponent model, EV calculation (including a regression test for the sunk-cost fix described in `decision/ev_calculator.py`), Monte Carlo equity estimation, the action space/legality rules, seed reproducibility, street threading through `observe()` (regression test for the fix described in Known Limitations), the empirical-Bayes opponent-stats shrinkage (`belief/opponent_stats.py`, also described in Known Limitations), and an end-to-end integration test that plays full hands through the real engine with the Bayesian agent. CI runs this suite on every push via GitHub Actions (see the badge above).

### Running with Docker
```bash
docker build -t bayesian-poker-agent .
docker run -p 5000:5000 -e FLASK_SECRET_KEY=$(openssl rand -hex 32) bayesian-poker-agent
```
This is the easiest way to deploy the web UI to a host like Render, Fly.io, or Railway for a live, shareable demo link.

---

## 📊 Statistics & Agent Types

The system ships with several agents to evaluate performance against:
*   **Random Agent**: Selects purely random actions. Used as an absolute baseline.
*   **EV Agent**: Plays "ABC" poker. It calculates EV but assumes the opponent's hole cards are completely random. Mathematically sound, but heavily exploitable.
*   **Bayesian Agent**: Dynamically updates its belief about the opponent's hand and runs EV calculations against a narrowed range instead of a uniform one, and adapts its fold/call assumptions to each opponent's actually-observed behavior as a match progresses (see Known Limitations). It convincingly outperforms the Random baseline, and **now beats the EV agent in expected value too** - though its raw win rate against EV stays under 50%, which is a real, explained property of its strategy rather than a contradiction (see below).

**Real Simulation Output (`main.py --hands 1500 --samples 50`, 5 seeds):**

| Matchup | Mean chip gain | Win rate | 95% CI |
|---|---|---|---|
| Bayesian vs EV | **+0.3297** | 44.43% | [0.0551, 0.6042] |
| Bayesian vs Random | +4.9238 | 46.85% | [4.3615, 5.4861] |
| EV vs Random | +5.6547 | 62.47% | [4.8516, 6.4577] |

So the actual ranking by expected value is **Bayesian > EV > Random**: with both fixes described in Known Limitations applied, the Bayesian agent's mean chip gain against the EV agent is positive with a 95% CI entirely above zero, and all 5 individual seeds were positive too - a consistent, reproducible result, not noise. Its win rate against EV (44.43%) is still below 50%, though: it wins fewer hands than it loses, but wins bigger ones, coming out ahead on chips overall - a legitimate value-betting/bluff-catching tradeoff once its opponent model is calibrated correctly, not a red flag. The same correction has a more mixed effect against Random: mean chip gain there is statistically unchanged from before the fix (overlapping 95% CIs), but win rate dropped from ~55% to ~47% - because Random has no stable behavioral pattern for the empirical correction to learn from, so it adds variance without adding signal for that specific opponent. This is a genuine, reproducible result of the current implementation, not a stale or cherry-picked number - see below for the root causes and fixes.

---

## ⚠️ Known Limitations

The Bayesian agent losing to the simpler EV agent was diagnosed down to two compounding root causes in the code. Both are now fixed and verified at full benchmark scale (see the table above):

1.  **A real bug, now fixed: `observe()` wasn't receiving the actual street.** `engine/game_engine.py` used to call `agents[1 - pid].observe(action)` with no `street` argument, and `BayesianAgent.observe(self, opponent_action, street=0)` silently defaulted to street `0` (preflop) for every call - so every postflop belief update was computed against the *preflop* row of the likelihood tables in `opponent_model.py`, regardless of what street the action actually happened on. **Fixed**: the engine now captures the street *before* `apply_action()` (since a check/call closing the street can advance it as a side effect) and passes it through - `agents[1 - pid].observe(action, street=acted_street)` - with `BaseAgent.observe()` widened to accept it and a regression test (`tests/test_observe_street_threading.py`) asserting the engine reports real, non-decreasing streets across a hand instead of always `0`. Verified on the real repo at a smaller/faster benchmark scale: Bayesian vs EV mean chip gain improved from -0.7302 to -0.5193 (win rate 44.50% -> 46.50%, same seeds). On its own this narrowed the gap without closing it - full-scale, it still left Bayesian vs EV mean chip gain at -0.7007 (95% CI [-1.0312, -0.3702]) - because item 2 below was still uncorrected.
2.  **A design limitation, now mitigated: the opponent archetype was a static, unlearned label.** `main.py` hard-codes `opponent_type="TIGHT"` when the Bayesian agent faces the EV agent. That label feeds fixed fold/call/bet-probability tables designed to describe a rule-based archetype (`TightAgent`-like behavior) - but `EVAgent` doesn't play like any hard-coded archetype; it best-responds to real Monte Carlo equity with no concept of hand buckets. Measuring `EVAgent`'s *actual* fold frequency by hand bucket and comparing it against the table the Bayesian agent assumes showed large, systematic gaps - for example, the model assumed a `TRASH`-bucket preflop opponent folds effectively 100% of the time under the TIGHT scaling, but `EVAgent` actually folds trash only about 12% of the time; the model assumed postflop `AIR` folds ~75-98% of the time, but `EVAgent` folds it under 10% of the time. Sweeping the opponent archetype (`TIGHT` / `LOOSE` / `AGGRESSIVE`) against the EV agent confirmed this wasn't a "wrong preset" problem: none of the three static labels let the Bayesian agent beat the EV agent, because the EV agent doesn't correspond to any fixed archetype at all.

    **Fix**: `belief/opponent_stats.py` adds an `OpponentStats` tracker that records the opponent's real fold vs. call/check responses per street across an entire match (it accumulates across all hands in a match and is deliberately *not* cleared by the per-hand `reset()`, unlike the hand-bucket belief). `decision/ev_calculator.compute_ev()`'s bet-EV branch now blends the static archetype-table prior with these empirical per-street rates via simple empirical-Bayes shrinkage (`blend_with_prior()`, prior worth 10 pseudo-observations): with zero real observations - e.g. a single hand, or a fresh web-UI session against a human - it's numerically identical to the old static-only behavior, and as a match accumulates hands, the fold/call estimate converges toward the opponent's true frequency, correcting exactly the mismatch measured above. This is a targeted empirical-Bayes patch to the fold/call estimate specifically, not a full learned opponent model - see Future Improvements for that.

    This is a real behavioral tradeoff, not a free lunch: because `RandomAgent` has no stable fold/call tendency for the tracker to learn (its actions are uniform noise by construction), the same correction adds variance rather than useful signal there - Bayesian vs Random's mean chip gain is statistically unchanged (95% CIs overlap, +4.9238 vs the pre-fix +5.2618) but its win rate dropped from ~55% to ~47%, the same expected value delivered through fewer, larger wins. Disclosed here rather than hidden, since it's an honest property of applying an empirical correction to an opponent with nothing consistent to correct toward.

With both root causes addressed, the Bayesian agent now beats the EV agent in expectation as well as beating Random, which was the original gap this section documented. The remaining honest caveat is scope: this fix corrects one scalar pair (fold/call rate) per street via shrinkage - it doesn't touch bet-sizing frequency, the hand-bucket likelihood tables themselves, or give the agent a genuinely *learned* representation of its opponent. A full **Dynamic RL Opponent Modeling** system (see below) remains the higher-ceiling next step.

## 🔮 Future Improvements

Because of the project's highly modular architecture, extending the system involves simply updating individual modules:

*   **Dynamic RL Opponent Modeling**: A lightweight empirical-Bayes correction for the fold/call rate specifically already exists (`belief/opponent_stats.py`, see Known Limitations). Go further: replace the hardcoded bet-sizing and hand-bucket likelihood tables in `opponent_model.py` with an Online Reinforcement Learning agent that learns an opponent's full playstyle over time, rather than shrinking one scalar pair toward observed frequency.
*   **Deep RL for Multi-Street Planning**: `ev_calculator.py` currently uses a greedy, one-step EV algorithm. Integrating Proximal Policy Optimization (PPO) would allow the agent to learn block betting or multi-street bluffs.
*   **Unsupervised Learning for Hand Bucketing**: Use clustering algorithms (like K-Means) to dynamically group hole cards by mathematical equity, rather than relying on static heuristic definitions.
*   **Exploitability / Ablation Studies**: Quantify what entropy-gated exploration actually contributes (Bayesian agent with it on vs. off), and estimate exploitability against a wider range of opponent strategies rather than only the bundled Random/EV/Tight agents.

---

## 🤝 Contributing
Contributions, issues, and feature requests are welcome! Feel free to check the issues page.

## 📝 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
