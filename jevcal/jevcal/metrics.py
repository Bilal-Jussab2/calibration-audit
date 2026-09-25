"""Metrics and the pass mark exactly as pre-registered. Pure functions, no I/O."""
from __future__ import annotations

import math
from dataclasses import dataclass, asdict

N_BINS = 10
Z95 = 1.959963984540054
ECE_MAX = 0.05
OVERCONF_MARGIN = 0.05
CONF_WRONG_THRESHOLD = 0.90


def wilson(k: int, n: int, z: float = Z95) -> tuple[float, float]:
    if n <= 0:
        raise ValueError("wilson interval needs n > 0")
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


@dataclass(frozen=True)
class Bin:
    index: int
    n: int
    mean_conf: float
    accuracy: float
    ci_low: float
    ci_high: float
    min_conf: float
    max_conf: float


def equal_mass_bins(conf: list[float], correct: list[bool], n_bins: int = N_BINS) -> list[Bin]:
    """Sort ascending by confidence; ties keep dataset order (stable sort)."""
    if len(conf) != len(correct):
        raise ValueError("conf and correct differ in length")
    n = len(conf)
    if n < n_bins:
        raise ValueError(f"need at least {n_bins} items, got {n}")
    order = sorted(range(n), key=lambda i: conf[i])  # Python sort is stable
    bins, start = [], 0
    for b in range(n_bins):
        size = n // n_bins + (1 if b < n % n_bins else 0)
        idx = order[start:start + size]
        start += size
        k = sum(correct[i] for i in idx)
        cs = [conf[i] for i in idx]
        lo, hi = wilson(k, size)
        bins.append(Bin(b, size, sum(cs) / size, k / size, lo, hi, min(cs), max(cs)))
    return bins


def ece(bins: list[Bin]) -> float:
    total = sum(b.n for b in bins)
    return sum(b.n * abs(b.mean_conf - b.accuracy) for b in bins) / total


def mce(bins: list[Bin]) -> float:
    return max(abs(b.mean_conf - b.accuracy) for b in bins)


def brier(prob_vectors: list[dict[str, float]], gold: list[str]) -> float:
    """Multiclass Brier: mean over items of sum_k (p_k - y_k)^2."""
    total = 0.0
    for probs, g in zip(prob_vectors, gold):
        total += sum((p - (1.0 if lab == g else 0.0)) ** 2 for lab, p in probs.items())
        if g not in probs:
            total += 1.0
    return total / len(gold)


@dataclass(frozen=True)
class PassMark:
    ece: float
    ece_ok: bool
    overconfident_bins: list[int]
    no_clear_overconfidence: bool
    top_vs_bottom_separated: bool
    passes: bool


def pass_mark(bins: list[Bin]) -> PassMark:
    e = ece(bins)
    over = [b.index for b in bins if b.ci_high < b.mean_conf - OVERCONF_MARGIN]
    top, bottom = bins[-1], bins[0]
    separated = top.ci_low > bottom.ci_high
    ok = e <= ECE_MAX and not over and separated
    return PassMark(e, e <= ECE_MAX, over, not over, separated, ok)


def verdict(original: PassMark, corrected: PassMark | None) -> str:
    """Pre-registered verdict table. Without hand-corrected labels the verdict is provisional."""
    if corrected is None:
        return "provisional: supported" if original.passes else "provisional: pending label review"
    if original.passes and corrected.passes:
        return "supported"
    if not original.passes and corrected.passes:
        return "inconclusive (failure comes from label errors)"
    if not original.passes and not corrected.passes:
        return "not supported on this test"
    return "supported"  # passes on original labels; corrected labels cannot undo that under the pre-registration


def confident_wrong_rate(conf: list[float], correct: list[bool], threshold: float = CONF_WRONG_THRESHOLD) -> tuple[int, int]:
    n_hi = sum(1 for c in conf if c >= threshold)
    n_wrong = sum(1 for c, ok in zip(conf, correct) if c >= threshold and not ok)
    return n_wrong, n_hi


def as_dict(obj) -> dict:
    return asdict(obj)
