"""
Data Scientist agent ("The Data Scientist"): an ENSEMBLE of the two other
model-driven agents -- EVAgent's pure pot-odds EV and BayesianAgent's
opponent-profiling EV -- blending their per-action value estimates and
picking the best. This is the real, final design for this seat, not a stand-in
for a heavier model that never shipped.

The blend weight isn't fixed. Early in a match, neither sub-model has real
signal on the opponents at this table, so the two are weighted evenly. As the
Bayesian sub-model accumulates real observations of the live opponents (via
its own OpponentStats, the same per-opponent tracking BayesianAgent uses to
adapt its opponent_type -- see _effective_opponent_type), its opponent-aware
read is trusted more: see _bayes_confidence().
"""

from typing import Any

from agents.base_agent import BaseAgent
from agents.ev_agent import EVAgent
from agents.bayesian_agent import BayesianAgent
from engine.action_space import get_legal_actions
from decision.strategy_mixer import select_action

# ponytail: fixed floor/ceiling on the blend weight rather than a learned
# function of confidence -- retune these two if the ensemble under/over-trusts
# the opponent read. Upgrade path: replace with a real trained model (see
# README's "Future Improvements") once there's self-play data to train on.
_BAYES_WEIGHT_FLOOR = 0.5
_BAYES_WEIGHT_CEILING = 0.7


class DataScientistAgent(BaseAgent):
    def __init__(self, player_id: int = 0, seed: int = None, epsilon: float = 0.04, samples: int = 120):
        self.player_id = player_id
        self._ev_model = EVAgent(player_id=player_id, epsilon=0.0, samples=samples, seed=seed)
        self._bayes_model = BayesianAgent(
            player_id=player_id, epsilon=0.0, samples=samples, seed=seed,
            opponent_type="LOOSE", forgetting_factor=0.02,
        )
        self.epsilon = epsilon
        import random
        self._rng = random.Random(seed)
        self._last_ev_dict = {}

    def reset(self) -> None:
        self._ev_model.reset()
        self._bayes_model.reset()

    def observe(self, opponent_action: str, street: int = 0, actor_id: int = None) -> None:
        # Only the Bayesian half of the ensemble actually tracks opponents.
        self._bayes_model.observe(opponent_action, street=street, actor_id=actor_id)

    def _bayes_confidence(self, game_state: Any) -> float:
        """How much weight the Bayesian sub-model's opponent-read gets this
        decision, vs. the EV model's blind pot-odds math: _BAYES_WEIGHT_FLOOR
        with no data on the live opponents, rising to _BAYES_WEIGHT_CEILING as
        they're observed past BayesianAgent's own adaptation floor
        (_ADAPT_MIN_HANDS) -- reusing its existing per-opponent stats rather
        than tracking confidence separately."""
        stats_by_opp = self._bayes_model._opponent_stats
        live_opponents = [pid for pid in game_state.live_players() if pid != self.player_id]
        observed_n = [
            agg[3]
            for pid in live_opponents
            if pid in stats_by_opp
            for agg in [stats_by_opp[pid].aggregate_rates()]
            if agg is not None
        ]
        if not observed_n:
            return _BAYES_WEIGHT_FLOOR
        avg_n = sum(observed_n) / len(observed_n)
        floor_hands = self._bayes_model._ADAPT_MIN_HANDS
        span = _BAYES_WEIGHT_CEILING - _BAYES_WEIGHT_FLOOR
        return _BAYES_WEIGHT_FLOOR + span * min(avg_n / floor_hands, 1.0)

    def act(self, game_state: Any) -> str:
        legal = get_legal_actions(game_state, self.player_id)
        if not legal:
            return "FOLD"

        # Run each sub-model's own act() first so its internal EV dict gets
        # populated the normal way, then blend the two dicts by confidence-
        # weighted average. (We call act() rather than duplicating EV math
        # here so both models go through their own already-verified
        # multiway/heads-up branching.)
        self._ev_model.act(game_state)
        self._bayes_model.act(game_state)
        ev_a = getattr(self._ev_model, "_last_ev_dict", {}) or {}
        ev_b = getattr(self._bayes_model, "_last_ev_dict", {}) or {}
        bayes_weight = self._bayes_confidence(game_state)
        ev_weight = 1.0 - bayes_weight
        self._last_bayes_weight = bayes_weight  # surfaced in decision/rationale.py

        blended = {}
        for a in legal:
            va = ev_a.get(a)
            vb = ev_b.get(a)
            if va is not None and vb is not None:
                blended[a] = ev_weight * va + bayes_weight * vb
            elif va is not None:
                blended[a] = va
            elif vb is not None:
                blended[a] = vb
            else:
                blended[a] = 0.0

        chosen = select_action(blended, legal, epsilon=self.epsilon, rng=self._rng)
        self._last_ev_dict = blended
        return chosen
