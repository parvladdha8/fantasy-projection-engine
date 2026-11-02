"""Tests for the opportunity × efficiency model."""

import numpy as np
import pandas as pd
import pytest

from fantasy_projection_engine.opp_eff import (
    DEFAULT_PARAMS, CompParams, add_components, decayed_prior_sum, league_rate, project,
)
from fantasy_projection_engine.player_games import STAT_COLS
from fantasy_projection_engine.scoring import ppr_points


def test_decayed_prior_sum_by_hand():
    # half-life 1 -> decay 0.5. Player A: x = 2, 4, 8. Prior sums: 0, 2, 0.5*2+4 = 5. Player B resets.
    out = decayed_prior_sum(np.array([2.0, 4.0, 8.0, 1.0]), np.array(["A", "A", "A", "B"]), 1)
    assert list(out) == [0.0, 2.0, 5.0, 0.0]


def _toy(n_weeks=6):
    rng = np.random.default_rng(0)
    rows = []
    for pid, pos in [("A", "WR"), ("B", "WR"), ("C", "RB")]:
        for w in range(1, n_weeks + 1):
            r = {c: 0.0 for c in STAT_COLS}
            r.update(targets=rng.integers(2, 10), carries=rng.integers(0, 15) if pos == "RB" else 0)
            r.update(receptions=r["targets"] // 2, receiving_yards=10.0 * r["targets"], rushing_yards=4.0 * r["carries"])
            rows.append({"player_id": pid, "position": pos, "season": 2019, "week": w, **r})
    d = pd.DataFrame(rows)
    d["actual"] = ppr_points(d)
    return d.sort_values(["player_id", "season", "week"]).reset_index(drop=True)


def test_components_sum_to_ppr():
    d = add_components(_toy())
    total = d[["pts_rec", "pts_rush", "pts_pass", "pts_other"]].sum(axis=1)
    np.testing.assert_allclose(total, d["actual"])


def test_league_rate_uses_only_earlier_weeks():
    d = add_components(_toy())
    mu = league_rate(d, "pts_rec", "targets")
    wk3 = (d["week"] == 3) & (d["position"] == "WR")
    early = d[(d["week"] < 3) & (d["position"] == "WR")]
    assert mu[wk3].iloc[0] == pytest.approx(early["pts_rec"].sum() / early["targets"].sum())
    assert mu[d["week"] == 1].isna().all()  # nothing earlier exists


def test_no_lookahead_any_player_same_week():
    """Changing ANY player's week-4 stats must not change any week ≤4 projection."""
    d = _toy()
    before = project(d)
    d2 = d.copy()
    d2.loc[d2["week"] == 4, ["targets", "receptions", "receiving_yards"]] *= 5
    after = project(d2)
    m = d["week"] <= 4
    pd.testing.assert_series_equal(before.loc[m, "proj"], after.loc[m, "proj"])
    assert not np.allclose(before.loc[d["week"] == 5, "proj"], after.loc[d["week"] == 5, "proj"])


def test_shrinkage_extremes():
    d = _toy()
    # huge k -> efficiency equals league average; k = 0 -> player's own rate
    big = project(d, {**DEFAULT_PARAMS, "rec": CompParams(4, 8, 1e9)})
    mu = league_rate(add_components(d), "pts_rec", "targets")
    m = big["eff_rec"].notna() & mu.notna()
    np.testing.assert_allclose(big.loc[m, "eff_rec"], mu[m], rtol=1e-6)
    assert (big.loc[m, "shrink_rec"] > 0.999).all()


def test_volume_shrinkage_m0_is_v1_and_large_m_is_long_run():
    d = _toy()
    v1 = project(d, {**DEFAULT_PARAMS, "rec": CompParams(3, 8, 25)})
    v2_m0 = project(d, {**DEFAULT_PARAMS, "rec": CompParams(3, 8, 25, hl_long=32, m=0)})
    pd.testing.assert_series_equal(v1["vol_rec"], v2_m0["vol_rec"])
    huge = project(d, {**DEFAULT_PARAMS, "rec": CompParams(3, 8, 25, hl_long=32, m=1e9)})
    g = d["player_id"].to_numpy()
    w = decayed_prior_sum(np.ones(len(d)), g, 32)
    long_run = decayed_prior_sum(d["targets"].to_numpy(float), g, 32) / np.where(w > 0, w, 1)
    m = w > 0
    np.testing.assert_allclose(huge.loc[m, "vol_rec"], long_run[m], rtol=1e-6)
