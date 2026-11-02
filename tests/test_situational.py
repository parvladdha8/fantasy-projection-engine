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


# ---- Week 1 effect (v11 / v11p) ----
from fantasy_projection_engine.situational import (
    fit_week1_players, fit_week1_position, lad_ratio, week1_multiplier,
)


def test_lad_ratio_is_weighted_median_of_ratios():
    x = np.array([1.0, 2.0, 3.0, 4.0])
    y = np.array([0.5, 4.0, 3.0, 6.0])  # ratios 0.5, 2, 1, 1.5 with weights 1, 2, 3, 4 → weighted median 1.5
    assert lad_ratio(y, x) == pytest.approx(1.5, abs=1e-3)


def test_position_effect_shrinks_noise_to_zero_and_keeps_a_real_effect():
    rng = np.random.default_rng(0)
    n = 400
    x = rng.uniform(5, 20, n)
    pos = np.repeat(["QB", "RB", "WR", "TE"], n // 4)
    games = np.arange(n) // 4
    noise = fit_week1_position(x * rng.lognormal(0, 0.5, n), x, pos, games, n_boot=100)
    assert (noise["B"] == 1).all() and (noise["gamma"] == 0).all()  # pure noise → shrunk fully to "no effect"
    eff = np.where(pos == "RB", 0.7, 1.0)  # RBs score 30% below the median projection in Week 1
    real = fit_week1_position(x * eff * rng.lognormal(0, 0.1, n), x, pos, games, n_boot=100).set_index("position")
    assert real.loc["RB", "gamma"] == pytest.approx(-0.3, abs=0.05)
    assert real.loc["RB", "B"] < 0.2


def test_player_effect_needs_repeated_openers():
    one_each = fit_week1_players(np.array([0.5, -0.4, 0.2]), np.array(["a", "b", "c"]), np.array(["WR"] * 3))
    assert (one_each["B"] == 1).all() and (one_each["dev"] == 0).all()
    rng = np.random.default_rng(1)
    true = {f"p{i}": rng.choice([-0.4, 0.4]) for i in range(40)}
    pid = np.repeat(list(true), 6)
    u = np.array([true[p] for p in pid]) + rng.normal(0, 0.1, len(pid))
    pl = fit_week1_players(u, pid, np.array(["WR"] * len(pid))).set_index("player_id")
    assert pl["B"].max() < 0.1  # strong, consistent player effects are barely shrunk
    np.testing.assert_allclose(pl["dev"], pd.Series(true)[pl.index], atol=0.1)


def test_week1_multiplier_walk_forward_and_week1_only():
    rng = np.random.default_rng(2)
    rows = [dict(season=s, week=w, position=p, player_id=f"{p}{i}", game_id=f"{s}_{w}_{i % 8}",
                 med=m, actual=m * 0.8 * rng.lognormal(0, 0.2))
            for s in (2019, 2020, 2021) for w in (1, 2) for p in ("RB", "WR") for i in range(40)
            for m in [rng.uniform(5, 20)]]
    d = pd.DataFrame(rows)
    mask = np.ones(len(d), bool)
    mult, pt, _ = week1_multiplier(d, "med", mask, n_boot=50)
    assert (mult[d.week != 1] == 1).all() and (mult[d.season == 2019] == 1).all()
    assert np.allclose(mult[(d.season == 2021) & (d.week == 1)], 0.8, atol=0.06)
    d2 = d.copy()
    d2.loc[d2.season == 2021, "actual"] *= 3  # the current season's outcomes must not matter
    np.testing.assert_allclose(week1_multiplier(d2, "med", mask, n_boot=50)[0], mult)
