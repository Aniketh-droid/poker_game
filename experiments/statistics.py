"""
Statistics: mean chip gain, std deviation, 95% confidence interval.
"""

import math
from typing import List


def mean(x: List[float]) -> float:
    if not x:
        return 0.0
    return sum(x) / len(x)


def std_dev(x: List[float], sample: bool = True) -> float:
    if len(x) < 2:
        return 0.0
    m = mean(x)
    variance = sum((v - m) ** 2 for v in x) / (len(x) - 1 if sample else len(x))
    return math.sqrt(variance)


def confidence_interval_95(x: List[float]) -> tuple:
    """Return (lower, upper) 95% CI for mean."""
    if len(x) < 2:
        return (mean(x), mean(x))
    n = len(x)
    m = mean(x)
    s = std_dev(x)
    # 1.96 for 95% CI
    margin = 1.96 * s / math.sqrt(n)
    return (m - margin, m + margin)


def report(chip_deltas: List[float]) -> dict:
    """Mean chip gain, std, 95% CI."""
    m = mean(chip_deltas)
    s = std_dev(chip_deltas)
    lo, hi = confidence_interval_95(chip_deltas)
    return {"mean": m, "std": s, "ci95_low": lo, "ci95_high": hi}


def summarize_runs(values: List[float]) -> dict:
    """Aggregate multiple run-level values with 95% CI."""
    m = mean(values)
    s = std_dev(values)
    lo, hi = confidence_interval_95(values)
    return {"mean": m, "std": s, "ci95_low": lo, "ci95_high": hi, "n": len(values)}
