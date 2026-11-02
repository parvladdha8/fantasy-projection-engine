"""Tests for median (LAD) calibration."""

import numpy as np
import pandas as pd
import pytest

from fantasy_projection_engine.calibration import median_calibration, quantile_fit


def test_lad_matches_brute_force_minimum():
    rng = np.random.default_rng(0)
    x = rng.uniform(5, 20, 400)
    y = 1 + 0.8 * x + rng.exponential(4, 400) - 4      # right-skewed noise
    X = np.column_stack([np.ones_like(x), x])
    b = quantile_fit(X, y)
    loss = lambda bb: np.abs(y - X @ bb).sum()
    best = min(((a, s) for a in np.linspace(-3, 3, 121) for s in np.linspace(0.5, 1.1, 121)), key=lambda bb: loss(np.array(bb)))
    assert loss(b) <= loss(np.array(best)) + 1e-6


def test_lad_targets_median_ols_targets_mean_under_skew():
    rng = np.random.default_rng(1)
    n = 20000
    x = rng.uniform(5, 20, n)
    y = x * rng.exponential(1, n)                      # mean = x, median = x·ln2
    X = np.column_stack([np.ones(n), x])
    assert quantile_fit(X, y)[1] == pytest.approx(np.log(2), abs=0.03)
    assert np.linalg.lstsq(X, y, rcond=None)[0][1] == pytest.approx(1.0, abs=0.03)


def test_quantiles_for_floor_and_ceiling():
    rng = np.random.default_rng(2)
    y = rng.normal(10, 3, 20000)
    X = np.ones((len(y), 1))
    assert quantile_fit(X, y, 0.1)[0] == pytest.approx(np.quantile(y, 0.1), abs=0.1)
    assert quantile_fit(X, y, 0.9)[0] == pytest.approx(np.quantile(y, 0.9), abs=0.1)


def test_calibration_is_walk_forward_and_per_position():
    rng = np.random.default_rng(3)
    n = 6000
    d = pd.DataFrame({"season": rng.choice([2019, 2020, 2021], n), "position": rng.choice(["WR", "TE"], n),
                      "proj": rng.uniform(5, 20, n)})
    d["actual"] = d["proj"] * np.where(d.position == "WR", 0.8, 1.0) + rng.normal(0, 1, n)
    out, coefs = median_calibration(d, "proj", np.ones(n, bool))
    assert np.allclose(out[(d.season == 2019).to_numpy()], d.loc[d.season == 2019, "proj"])   # nothing earlier
    c = coefs.set_index(["season", "position"])
    assert c.loc[(2021, "WR"), "b"] == pytest.approx(0.8, abs=0.03)
    assert c.loc[(2021, "TE"), "b"] == pytest.approx(1.0, abs=0.03)
    d2 = d.copy()
    d2.loc[d2.season == 2021, "actual"] *= 3
    np.testing.assert_allclose(median_calibration(d2, "proj", np.ones(n, bool))[0], out)


def test_multiplicative_map_has_no_intercept_and_finds_median_ratio():
    rng = np.random.default_rng(4)
    n = 20000
    d = pd.DataFrame({"season": rng.choice([2019, 2020], n), "position": "RB", "proj": rng.uniform(0, 20, n)})
    d["actual"] = d["proj"] * rng.exponential(1, n)                 # median ratio = ln 2
    out, coefs = median_calibration(d, "proj", np.ones(n, bool), "lad_mult")
    c = coefs.set_index("season").loc[2020]
    # exact answer: min Σ|y − b·x| (x > 0) is the x-weighted median of y/x over the training rows (2019)
    t = d[d.season == 2019]
    r = (t.actual / t.proj).to_numpy()
    o = np.argsort(r)
    cw = np.cumsum(t.proj.to_numpy()[o])
    exact = r[o][np.searchsorted(cw, cw[-1] / 2)]
    assert c["a"] == 0 and c["b"] == pytest.approx(exact, abs=1e-4)
    assert c["b"] == pytest.approx(np.log(2), abs=0.05)               # population median ratio
    s20 = (d.season == 2020).to_numpy()
    np.testing.assert_allclose(out[s20], c["b"] * d.loc[s20, "proj"])
