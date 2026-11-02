"""Tests for the week-of-season effect (shrinkage math and walk-forward)."""

import numpy as np
import pandas as pd
import pytest

from fantasy_projection_engine.situational import fit_week_effects, week_multiplier, week_phase


def _games(late_effect=-0.10, n_per_week=400, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for season in [2019, 2020, 2021]:
        for week in range(1, 19):
            proj = rng.uniform(8, 20, n_per_week)
            true = 1 + (late_effect if week >= 13 else 0)
            rows.append(pd.DataFrame({"season": season, "week": week, "position": "WR", "proj": proj,
                                      "actual": proj * true + rng.normal(0, 6, n_per_week)}))
    return pd.concat(rows, ignore_index=True)


def test_phases():
    assert week_phase(pd.Series([1, 4, 5, 12, 13, 18])).tolist() == ["early", "early", "mid", "mid", "late", "late"]


def test_recovers_late_season_effect():
    d = _games()
    t = fit_week_effects(d, "proj", np.ones(len(d), bool)).set_index("phase")
    assert t.loc["late", "gamma"] == pytest.approx(-0.10, abs=0.01)
    assert abs(t.loc["mid", "gamma"]) < 0.01
    assert t.loc["late", "B"] < 0.05  # strong, well-measured effect → barely shrunk


def test_no_true_effect_is_shrunk_to_position_mean():
    d = _games(late_effect=0.0, n_per_week=20)
    t = fit_week_effects(d, "proj", np.ones(len(d), bool))
    assert t["B"].min() > 0.5           # pure noise → mostly shrunk
    assert np.ptp(t["gamma"]) < np.ptp(t["raw"])


def test_pos_control_has_no_phase_variation():
    d = _games()
    t = fit_week_effects(d, "proj", np.ones(len(d), bool), mode="pos")
    assert np.ptp(t["gamma"]) == 0


def test_walk_forward():
    d = _games()
    m1, _ = week_multiplier(d, "proj", np.ones(len(d), bool))
    d2 = d.copy()
    d2.loc[d2["season"] == 2021, "actual"] *= 5     # change the LAST season's outcomes
    m2, _ = week_multiplier(d2, "proj", np.ones(len(d), bool))
    np.testing.assert_allclose(m1, m2)
    assert np.all(m1[(d["season"] == 2019).to_numpy()] == 1)  # first season: nothing earlier
