import math
import random

import pytest

from jevcal import metrics as M


def test_wilson_matches_known_value():
    lo, hi = M.wilson(277, 308)  # ~90%
    assert math.isclose((hi - lo) / 2, 0.034, abs_tol=0.002)


def test_wilson_edges_and_bad_input():
    assert math.isclose(M.wilson(0, 10)[0], 0.0, abs_tol=1e-12)
    assert math.isclose(M.wilson(10, 10)[1], 1.0, abs_tol=1e-12)
    with pytest.raises(ValueError):
        M.wilson(0, 0)


def test_equal_mass_bins_sizes_and_stable_ties():
    conf = [0.5] * 3080
    correct = [i % 2 == 0 for i in range(3080)]
    bins = M.equal_mass_bins(conf, correct)
    assert [b.n for b in bins] == [308] * 10
    assert all(b.accuracy == 0.5 for b in bins)  # stable order keeps alternation


def test_uneven_split_distributes_remainder():
    bins = M.equal_mass_bins([i / 23 for i in range(23)], [True] * 23)
    assert sum(b.n for b in bins) == 23 and max(b.n for b in bins) - min(b.n for b in bins) == 1


def test_perfectly_calibrated_model_passes():
    rng = random.Random(1)
    conf = [rng.uniform(0.2, 1.0) for _ in range(20000)]
    correct = [rng.random() < c for c in conf]
    pm = M.pass_mark(M.equal_mass_bins(conf, correct))
    assert pm.ece < 0.02 and pm.passes


def test_overconfident_model_fails():
    rng = random.Random(2)
    conf = [rng.uniform(0.8, 1.0) for _ in range(5000)]
    correct = [rng.random() < c - 0.15 for c in conf]
    pm = M.pass_mark(M.equal_mass_bins(conf, correct))
    assert not pm.ece_ok and pm.overconfident_bins and not pm.passes


def test_constant_confidence_trick_is_caught_by_separation():
    # every answer at 0.9, accuracy 0.9: tiny ECE but confidence says nothing
    conf = [0.9] * 3080
    correct = [i % 10 != 0 for i in range(3080)]
    pm = M.pass_mark(M.equal_mass_bins(conf, correct))
    assert pm.ece_ok and not pm.top_vs_bottom_separated and not pm.passes


def test_brier_bounds():
    assert M.brier([{"a": 1.0, "b": 0.0}], ["a"]) == 0.0
    assert M.brier([{"a": 1.0, "b": 0.0}], ["b"]) == 2.0


def test_verdict_table():
    p = M.PassMark(0.01, True, [], True, True, True)
    f = M.PassMark(0.2, False, [9], False, True, False)
    assert M.verdict(p, p) == "supported"
    assert M.verdict(f, p).startswith("inconclusive")
    assert M.verdict(f, f) == "not supported on this test"


def test_confident_wrong_rate():
    assert M.confident_wrong_rate([0.95, 0.95, 0.5], [True, False, False]) == (1, 2)
