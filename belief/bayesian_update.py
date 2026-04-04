"""
Bayesian belief update: posterior ∝ likelihood × prior, normalize, then smooth ε = 0.01.
Smoothing is applied AFTER normalization (Laplace-style) so it acts as a floor
on the final distribution rather than swamping the likelihood signal before normalization.
"""
 
from typing import Dict, Any
 
from belief.opponent_model import likelihood_action_given_bucket
 
EPSILON = 0.01  # Reduced from 0.05; applied post-normalization
 
 
def update_belief(
    prior: Dict[str, float],
    action: str,
    context: Any,
    opponent_type: str = "TIGHT",
) -> Dict[str, float]:
    """
    Compute posterior ∝ likelihood × prior, normalize, then apply smoothing ε.
    Smoothing is now post-normalization: posterior = (1 - ε) * normalized + ε * uniform.
    This prevents EPSILON from swamping likelihood differences before normalization.
    context must have .street (and optionally other fields).
    """
    street = getattr(context, "street", 0)
 
    raw = {}
    for bucket in prior:
        lk = likelihood_action_given_bucket(action, bucket, street, opponent_type)
        raw[bucket] = prior[bucket] * lk
 
    total = sum(raw.values())
    if total <= 0:
        n = len(prior)
        return {b: 1.0 / n for b in prior}
 
    # Normalize first
    normalized = {b: raw[b] / total for b in raw}
 
    # Then apply smoothing toward uniform (post-normalization)
    n = len(normalized)
    uniform = 1.0 / n if n > 0 else 0.0
    smoothed = {
        b: (1.0 - EPSILON) * normalized[b] + EPSILON * uniform
        for b in normalized
    }
 
    # Re-normalize after smoothing (smoothed already sums to 1 but guard for float drift)
    s = sum(smoothed.values())
    return {b: smoothed[b] / s for b in smoothed}
 