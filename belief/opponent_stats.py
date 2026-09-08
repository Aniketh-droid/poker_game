"""
Empirical opponent action-frequency tracker.

WHY THIS EXISTS: belief/opponent_model.py's likelihood tables are scaled by a
single static `opponent_type` label (TIGHT/LOOSE/AGGRESSIVE) that is *chosen
once at agent construction* and never adapts. That's a reasonable prior when
nothing else is known, but it silently mismatches any opponent whose real
behavior doesn't fit one of those three fixed archetypes -- notably EVAgent,
which is a pure Monte-Carlo-equity maximizer with no folding discipline or
"type" at all. When compute_ev() estimates P(opponent folds/calls | I bet),
it was using ONLY that static, possibly-wrong prior, which biases the
Bayesian agent's betting/checking decisions against opponents the archetype
table doesn't describe well.

OpponentStats tracks how the opponent has actually responded (fold vs
call/check), bucketed by street, over the course of a match (many hands
against the same opponent instance). BayesianAgent feeds observed actions
into it from observe() and does NOT reset it between hands (unlike belief,
which is a per-hand quantity) -- so it accumulates real signal about this
specific opponent across the whole match. decision.ev_calculator.compute_ev
then blends this empirical estimate with the static archetype prior via
simple empirical-Bayes shrinkage: with few observations the blend stays close
to the prior (so a fresh match behaves exactly as before), and as more hands
are observed it converges toward the opponent's real fold/call frequency.
"""

from typing import Optional, Tuple

from engine.action_space import FOLD, CHECK, CALL

_NUM_STREETS = 4  # preflop, flop, turn, river


class OpponentStats:
    """Per-street empirical fold/call counts for one opponent, accumulated
    across an entire match (persists across hands; NOT reset per hand)."""

    def __init__(self) -> None:
        self._fold_count = [0] * _NUM_STREETS
        self._call_count = [0] * _NUM_STREETS
        self._total_count = [0] * _NUM_STREETS

    def record(self, action: str, street: int) -> None:
        """Record one observed opponent action at the given street.
        Only fold vs call/check are tracked -- bet-sizing choice isn't needed
        for the fold_prob/call_prob estimate compute_ev uses."""
        street = min(max(street, 0), _NUM_STREETS - 1)
        self._total_count[street] += 1
        if action == FOLD:
            self._fold_count[street] += 1
        elif action in (CHECK, CALL):
            self._call_count[street] += 1
        # Bet/raise actions count toward the total (so fold/call rates are
        # correctly out of all responses) but neither counter directly.

    def empirical_rates(self, street: int) -> Optional[Tuple[float, float, int]]:
        """Return (fold_rate, call_rate, n_observations) at this street, or
        None if nothing has been observed there yet."""
        street = min(max(street, 0), _NUM_STREETS - 1)
        n = self._total_count[street]
        if n == 0:
            return None
        return self._fold_count[street] / n, self._call_count[street] / n, n

    def aggregate_rates(self) -> Optional[Tuple[float, float, float, int]]:
        """Return (fold_rate, call_rate, bet_rate, n) across every street
        observed so far this match, or None with no observations yet. Used to
        classify an opponent's overall archetype once enough hands have been
        played (see BayesianAgent._effective_opponent_type)."""
        n = sum(self._total_count)
        if n == 0:
            return None
        fold_rate = sum(self._fold_count) / n
        call_rate = sum(self._call_count) / n
        bet_rate = max(0.0, 1.0 - fold_rate - call_rate)
        return fold_rate, call_rate, bet_rate, n


def blend_with_prior(
    prior_fold: float,
    prior_call: float,
    empirical: Optional[Tuple[float, float, int]],
    prior_weight: float = 10.0,
) -> Tuple[float, float]:
    """
    Empirical-Bayes shrinkage: treat the static archetype prior as worth
    `prior_weight` pseudo-observations, and blend it with the real observed
    (fold_rate, call_rate, n) using simple weighted averaging. With n=0 this
    returns the prior unchanged; as n grows past prior_weight, the empirical
    rate dominates.
    """
    if empirical is None:
        return prior_fold, prior_call
    emp_fold, emp_call, n = empirical
    total_weight = prior_weight + n
    if total_weight <= 0:
        return prior_fold, prior_call
    fold_prob = (prior_weight * prior_fold + n * emp_fold) / total_weight
    call_prob = (prior_weight * prior_call + n * emp_call) / total_weight
    return fold_prob, call_prob
