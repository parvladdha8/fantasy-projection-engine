"""Tests for interval metrics (coverage, interval score)."""

import numpy as np
import pytest

from fantasy_projection_engine.metrics import coverage, interval_score


def test_coverage_counts():
    c = coverage([1, 5, 9, 12], [2, 2, 2, 2], [10, 10, 10, 10])
    assert c == {"inside": 0.5, "below": 0.25, "above": 0.25}


def test_interval_score_by_hand():
    # inside: width only; below by 2: width + 10·2; above by 1: width + 10·1
    s = interval_score([5, 0, 11], [2, 2, 2], [10, 10, 10])
    np.testing.assert_allclose(s, [8, 28, 18])


def test_interval_score_is_minimised_by_true_quantiles():
    rng = np.random.default_rng(0)
    y = rng.exponential(10, 200000)
    true = np.quantile(y, [0.1, 0.9])
    best = interval_score(y, *true).mean()
    for lo, hi in [(true[0] * 0.7, true[1]), (true[0], true[1] * 1.3), (true[0] * 1.3, true[1] * 0.8)]:
        assert interval_score(y, lo, hi).mean() > best
