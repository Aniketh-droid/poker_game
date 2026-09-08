# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Existing codebase, not a greenfield decision: Flask backend (`app.py`) serving a
single-page frontend built in hand-written HTML/CSS/vanilla JS (`static/`), no
frontend framework or build step. Python poker engine, belief, and decision
modules under `engine/`, `belief/`, `decision/`, `evaluation/`, `agents/`.
Runtime deps: `flask` only. Deployable via the included `Dockerfile`.

## Users

Three audiences that matter roughly equally, all arriving via the GitHub repo
(README first; the app is run locally by those who clone it, or from a hosted
demo link if one is later published):

- **Technical evaluators / recruiters** skimming the repo to judge engineering
  and applied-ML craft.
- **People who want to play** a genuinely fun single-player No-Limit Hold'em
  game against bots with distinct, non-random styles.
- **Curious technical visitors** drawn to inspectable AI decision-making — the
  "why did they play that way?" rationale is a hook, not a footnote.

No single audience is primary; design and copy should serve all three without
collapsing into any one (pure portfolio piece, pure game, or pure demo).

## Product Purpose

A playable No-Limit Texas Hold'em web app: sit at a configurable 2–6 player
table against a roster of AI opponents that each play a genuinely different,
model-backed style, from a Monte-Carlo EV grinder to a per-seat Bayesian
opponent-profiler that reads you better the longer you play. It began as a
2-player academic benchmark comparing decision models and became a game.
Success: a visitor plays multiple hands, understands that the bots are distinct
and inspectable (not neural black boxes), and comes away with a higher opinion
of the underlying work.

## Positioning

Every bot decision traces back to an inspectable expected-value calculation —
no neural-network black boxes. The engine and "The Profiler"'s per-opponent
belief tracking are real, stress-tested engineering, not a demo veneer — see
the README's "Key Features" and "Core Architecture" sections for the specifics
(per-seat Bayesian modeling, side-pot math, multiway all-in run-outs).

## Operating Context

- Two entry surfaces: the README on GitHub, then the running app (local
  `python app.py` → `localhost:5000`, or a hosted container).
- The app runs a persistent multi-hand match per browser session: stacks carry
  over, the button rotates, play continues until the human busts, the table
  busts, or the player leaves.
- Two screens today: table setup (pick size + opponents, or "Deal Me In" to fill
  randomly) and the live table (felt, seats, board, pot, hero action panel,
  "Table Talk" taunt log, post-hand result banner with decision rationale).
- One surface: the web app. The original CLI research tooling (`play_human.py`,
  `main.py`, `experiments/`) has been archived out of this repo (kept locally,
  not tracked in git) — see "Evidence on Hand" for what it produced.

## Capabilities and Constraints

- 2–6 handed tables; opponents chosen from a fixed roster of 7 personalities
  (Wildcard, The Rock, Calling Station, The Mathematician, The Maniac, The
  Profiler, The Data Scientist), each mapped to a real decision agent.
- Personality layer (`agents/personalities.py`) is purely presentational —
  avatar, tagline, difficulty, situational taunts keyed by trigger (bet, raise,
  call, fold, check, win, lose, bad_beat, bluff_win, idle) — decoupled from
  decision logic.
- Per-session isolated game state on the Flask backend; multiple people can play
  concurrent independent matches.
- "The Data Scientist" is a confidence-weighted EV+Bayesian ensemble: it
  weighs the two sub-models evenly with no data on the table, and trusts the
  Bayesian opponent-read more as real observations of the live opponents
  accumulate (see `_bayes_confidence()`).
- Multiway EV uses a deliberate simplification ("everyone folds" = product of
  individual fold probabilities), not a full game-theoretic solve — an
  acknowledged fun-first tradeoff, not a research claim.
- Terminology: "roster", "seat", "the felt", "Table Talk", "Deal Me In", "hero"
  (the human player), "hand meta", "run-out", "side pot".

## Brand Commitments

- Name: **Bluff & Bayes**. Keep it.
- Visual identity: the **"Card-Room Ledger"** system in `DESIGN.md` — a private
  card room kept as a hand-inked ledger (baize green, aged paper, oxblood,
  brass, Caslon display type) — replaced the earlier dark-casino/neon-gradient
  look and is implemented across `static/index.html`/`app.js`/`styles.css`,
  including the bot silhouette portraits in `static/portraits.js`. Not fixed
  forever, but this is the shipped identity going forward, not a draft.
- Voice in-product is playful and characterful (every bot talks trash); README
  voice is confident, precise, and forthcoming about limitations.

## Evidence on Hand

- Real, runnable product: full engine, agents, Flask app, test suite, CI badge.
- Benchmark results with 95% confidence intervals in the README (produced by
  the now-archived `main.py`, 1500 hands × 5 seeds): Bayesian > EV > Random by
  expected value — documented as a historical research finding, not a live demo.
- Screenshots: `static/screenshots/` (predate the Card-Room Ledger redesign —
  see the pivot log's Round 7 note; still owed a refresh).
- No customer testimonials, usage numbers, press, or awards — future work must
  not fabricate any.

## Product Principles

1. **Every decision is inspectable.** The value proposition is legible AI, not a
   strong opponent — surface the reasoning, don't hide it.
2. **The bots are characters.** Distinct styles and trash talk are core to the
   experience, not decoration; the roster is the product's cast.
3. **Fun-first, honest about scope.** Deliberate simplifications are disclosed,
   never hidden; the app is a game, not a claim of GTO optimality.
4. **Serve all three audiences at once.** Evaluators, players, and the curious
   should each find their reason to stay without the design picking a side.
5. **The felt is the stage.** The live table is where the product proves itself;
   everything else exists to get the visitor there and explain what they saw.

## Accessibility & Inclusion

No product-specific standard has been established. General baseline applies.
The Card-Room Ledger palette (paper/ink/oxblood/brass, see `DESIGN.md`) still
leans on color to carry state (e.g. gain-green vs. oxblood); future work
should add non-color cues rather than deepen that reliance.
