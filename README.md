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
The suite covers the hand evaluator, hand bucketing, the Bayesian belief update, the opponent model, EV calculation (including a regression test for the sunk-cost fix described in `decision/ev_calculator.py`), Monte Carlo equity estimation, the action space/legality rules, seed reproducibility, and an end-to-end integration test that plays full hands through the real engine with the Bayesian agent. CI runs this suite on every push via GitHub Actions (see the badge above).

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
*   **Bayesian Agent**: The star of the project. Dynamically updates its opponent ranges and uses precise EV calculations against a narrowed-down range to extract maximum value and make elite folds.

**Sample Simulation Output (`main.py`):**
When simulating the Bayesian Agent against the EV agent across 1,500 hands:
*   `Mean chip gain: 4.4714 (95% CI [3.2955, 5.6473])`
*   *Interpretation*: The 95% Confidence Interval is heavily above 0, statistically proving the Bayesian agent exhibits superior, non-random exploitation skills.

Note that this result is measured against EV/Random agents that the Bayesian agent's belief model is well-suited to exploit; it isn't a claim of solver-level (Nash-approximate) play. See Future Improvements below.

---

## 🔮 Future Improvements

Because of the project's highly modular architecture, extending the system involves simply updating individual modules:

*   **Dynamic RL Opponent Modeling**: Replace the hardcoded likelihood tables in `opponent_model.py` with an Online Reinforcement Learning agent that learns an opponent's specific psychological playstyle over time.
*   **Deep RL for Multi-Street Planning**: `ev_calculator.py` currently uses a greedy, one-step EV algorithm. Integrating Proximal Policy Optimization (PPO) would allow the agent to learn block betting or multi-street bluffs.
*   **Unsupervised Learning for Hand Bucketing**: Use clustering algorithms (like K-Means) to dynamically group hole cards by mathematical equity, rather than relying on static heuristic definitions.
*   **Exploitability / Ablation Studies**: Quantify what entropy-gated exploration actually contributes (Bayesian agent with it on vs. off), and estimate exploitability against a wider range of opponent strategies rather than only the bundled Random/EV/Tight agents.

---

## 🤝 Contributing
Contributions, issues, and feature requests are welcome! Feel free to check the issues page.

## 📝 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
