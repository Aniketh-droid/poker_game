"""
Data Scientist agent ("The Data Scientist"): meant to be backed by a DataRobot
AutoML model trained on self-play data (predict per-action value, pick the best).

STATUS: DataRobot's API (app.datarobot.com) is blocked by this environment's
network egress policy, both from the cloud sandbox and the linked device --
confirmed via a direct connection test, not assumed. Training/deploying the
real AutoML model is therefore on hold pending either an org admin allowlisting
that host, or someone running the training step outside this sandbox (see
README for the prepared data-gen script and instructions).

Rather than ship a personality that's just disabled, this class is a genuine
interim bot: an ENSEMBLE of the two existing model-driven agents (EVAgent's
pure pot-odds EV and BayesianAgent's opponent-profiling EV), averaging their
per-action EV estimates and picking the best. This is a real, if simpler,
"data-driven blend" -- not a placeholder that always folds or plays randomly --
so the personality is fully playable today.

SWAP-IN PATH for when DataRobot access is available: replace the body of
`_ensemble_ev()` (or act() entirely) with a call through datarobot-predict's
scoring code / a deployment's predict_proba, feeding it the same feature
vector the self-play data generator produces (see experiments/ once written).
Everything else here -- legal-action filtering, action selection, the
BaseAgent interface -- stays the same, so no caller needs to change.
"""

from typing import Any

from agents.base_agent import BaseAgent
from agents.ev_agent import EVAgent
from agents.bayesian_agent import BayesianAgent
from engine.action_space import get_legal_actions
from decision.strategy_mixer import select_action


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

    def act(self, game_state: Any) -> str:
        legal = get_legal_actions(game_state, self.player_id)
        if not legal:
            return "FOLD"

        # Run each sub-model's own act() first so its internal EV dict gets
        # populated the normal way, then blend the two dicts by simple average.
        # (We call act() rather than duplicating EV math here so both models
        # go through their own already-verified multiway/heads-up branching.)
        self._ev_model.act(game_state)
        self._bayes_model.act(game_state)
        ev_a = getattr(self._ev_model, "_last_ev_dict", {}) or {}
        ev_b = getattr(self._bayes_model, "_last_ev_dict", {}) or {}

        blended = {}
        for a in legal:
            va = ev_a.get(a)
            vb = ev_b.get(a)
            if va is not None and vb is not None:
                blended[a] = 0.5 * va + 0.5 * vb
            elif va is not None:
                blended[a] = va
            elif vb is not None:
                blended[a] = vb
            else:
                blended[a] = 0.0

        chosen = select_action(blended, legal, epsilon=self.epsilon, rng=self._rng)
        self._last_ev_dict = blended
        return chosen
