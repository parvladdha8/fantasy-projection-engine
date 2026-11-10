"""Tests for Big 60 scoring on made-up data."""

import numpy as np
import pandas as pd
import pytest

from fantasy_projection_engine.leaderboard import big60, score_week, season_record


def _week(seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for pos, n in {"QB": 15, "RB": 30, "WR": 30, "TE": 15}.items():
        for i in range(n):
            rows.append({"player_id": f"{pos}{i}", "position": pos, "projected": float(30 - i)})
    plat = pd.DataFrame(rows)
    ours = plat.assign(projected=plat["projected"] + rng.normal(0, 2, len(plat)))
    act = plat[["player_id"]].assign(points_ppr=plat["projected"] + rng.normal(0, 6, len(plat)))
    return plat, ours, act


def test_pool_is_platforms_own_top60_never_actual_points():
    plat, ours, act = _week()
    act["points_ppr"] = -plat["projected"]          # actual points opposite to projections: pool must not change
    pool, n_inactive = big60(plat)
    assert len(pool) == 60 and n_inactive == 0
    assert pool.groupby("position").size().to_dict() == {"QB": 10, "RB": 20, "WR": 20, "TE": 10}
    assert set(pool[pool.position == "QB"].player_id) == {f"QB{i}" for i in range(10)}


def test_inactive_removed_before_selection_keeps_60():
    plat, ours, act = _week()
    pool, n_inactive = big60(plat, inactive_ids=["QB0", "WR3"])
    assert len(pool) == 60 and n_inactive == 2
    assert "QB0" not in set(pool.player_id) and "QB10" in set(pool.player_id)   # next man up


def test_metrics_and_missing_policies():
    plat, ours, act = _week()
    ours = ours[ours.player_id != "RB0"]               # we have no projection for RB0
    act = act[act.player_id != "WR1"]                  # WR1 active, no stat line → 0 points
    w, pos, t = score_week(plat, ours, act, platform="baseline")
    assert w["n_pool"] == 60 and w["n_dropped_no_ours"] == 1 and w["n_scored"] == 59
    assert t.loc[t.player_id == "WR1", "actual"].item() == 0.0
    assert w["mae_ours"] == pytest.approx((t.ours - t.actual).abs().mean())
    assert w["winner"] == ("ours" if w["mae_ours"] < w["mae_platform"] else "platform")
    assert pos["n"].sum() == 59


def test_tie_and_running_record():
    plat, _, act = _week()
    w, _, _ = score_week(plat, plat, act)              # identical projections → tie
    assert w["winner"] == "tie"
    weekly = pd.DataFrame({"platform": "baseline", "season": 2026, "week": [1, 2, 3, 4],
                           "winner": ["ours", "platform", "tie", "ours"]})
    assert season_record(weekly)["record"].tolist() == ["1–0", "1–1", "1–1–1", "2–1–1"]


def test_highlights_names_only_ranked_by_margin():
    from fantasy_projection_engine.leaderboard import highlights
    t = pd.DataFrame({"player_id": ["a", "b", "c", "d"], "position": ["QB", "RB", "WR", "TE"],
                      "err_ours": [1.0, 2.0, 9.0, 4.0], "err_theirs": [8.0, 3.0, 2.0, 4.0]})
    h = highlights(t, "sleeper", n=5)
    assert list(h.columns) == ["platform", "kind", "rank", "player_id", "position"]   # no errors, no projections
    assert h[h.kind == "win"].player_id.tolist() == ["a", "b"]    # a: 7 pts closer, b: 1 pt closer
    assert h[h.kind == "loss"].player_id.tolist() == ["c"]        # c: 7 pts further; d tied → neither
    assert h[h.kind == "win"]["rank"].tolist() == [1, 2]
