"""Tests for the single prediction function and its explanation waterfall."""

import json

import numpy as np
import pandas as pd
import pytest

from fantasy_projection_engine import TEST_SEASON
from fantasy_projection_engine.opp_eff import add_components
from fantasy_projection_engine.player_games import STAT_COLS
from fantasy_projection_engine.predict import CONFIG_PATH, STEPS, explanation_table, load_model, predict
from fantasy_projection_engine.scoring import ppr_points

ROSTER = [("QB", 1), ("RB", 2), ("WR", 3), ("TE", 1)]


def _league(seasons=(2023, 2024, 2025), n_teams=4, weeks=17, seed=0):
    """A toy league with every column predict() needs. Seasons end at TEST_SEASON on purpose."""
    rng = np.random.default_rng(seed)
    rows = []
    for s in seasons:
        for w in range(1, weeks + 1):
            for t in range(n_teams):
                implied = rng.uniform(16, 29)
                margin = rng.uniform(-8, 8) * (1 if t % 2 == 0 else -1)
                for pos, n in ROSTER:
                    for j in range(n):
                        r = {c: 0.0 for c in STAT_COLS}
                        skill = 1.0 + 0.3 * j
                        if pos == "QB":
                            att = rng.poisson(20 + 0.5 * implied)
                            r.update(attempts=att, passing_yards=rng.normal(7, 1) * att,
                                     passing_tds=rng.poisson(implied / 12), carries=rng.poisson(3), rushing_yards=rng.normal(12, 8))
                        if pos == "RB":
                            r.update(carries=rng.poisson(14 / skill), rushing_yards=rng.normal(4.2, 1) * 14 / skill,
                                     rushing_tds=rng.poisson(implied / 50), targets=rng.poisson(3 / skill))
                        if pos in ("WR", "TE"):
                            r.update(targets=rng.poisson((8 if pos == "WR" else 5) / skill))
                        for c in ("attempts", "carries", "targets"):  # rare trick plays, as in the real league
                            r[c] = r[c] or float(rng.poisson(0.2))
                        if r["targets"]:
                            r["receptions"] = rng.binomial(int(r["targets"]), 0.65)
                            r["receiving_yards"] = rng.normal(11, 3) * r["receptions"]
                            r["receiving_tds"] = rng.poisson(implied / 90 * r["receptions"] / 4)
                        rows.append({"player_id": f"T{t}{pos}{j}", "player_display_name": f"T{t} {pos}{j}", "position": pos,
                                     "team": f"T{t}", "season": s, "week": w, "game_id": f"{s}_{w:02d}_{t // 2}",
                                     "implied": implied, "margin": margin, **r})
    d = pd.DataFrame(rows)
    for c in ("attempts", "carries", "targets"):
        d[f"team_{c}"] = d.groupby(["team", "game_id"])[c].transform("sum")
    d["actual"] = ppr_points(d)
    d["hist"], d["source"] = d["actual"], "stats"
    return add_components(d.sort_values(["player_id", "season", "week"]).reset_index(drop=True))


@pytest.fixture(scope="module")
def league():
    return _league()


@pytest.fixture(scope="module")
def pred(league):
    return predict(league, allow_test=True)


def test_waterfall_adds_up_to_median(pred):
    """baseline + Σ deltas = median, exactly, for every explainable player-game."""
    ok = pred[[f"step_{k}" for k, _ in STEPS]].notna().all(axis=1)
    assert ok.mean() > 0.9
    total = pred.loc[ok, [f"delta_{k}" for k, _ in STEPS]].sum(axis=1)
    np.testing.assert_allclose(total, pred.loc[ok, "median"], atol=1e-9)
    assert (pred.loc[ok, "step_lines_eff"] == pred.loc[ok, "step_median"] - pred.loc[ok, "delta_median"]).all()


def test_floor_median_ceiling_ordered(pred):
    d = pred.dropna(subset=["floor", "ceiling", "median"])
    assert len(d) > 500  # the last season has fitted bands
    assert (d["floor"] <= d["median"]).all() and (d["median"] <= d["ceiling"]).all()


def test_no_lookahead_truncating_the_future_changes_nothing(league, pred):
    """Projections for 2025 week 8 are identical whether or not weeks 9+ exist in the data."""
    cut = league[(league["season"] < 2025) | (league["week"] <= 8)].reset_index(drop=True)
    short = predict(cut, allow_test=True)
    cols = ["median", "floor", "ceiling"] + [f"step_{k}" for k, _ in STEPS]
    a = pred[(pred.season == 2025) & (pred.week == 8)].set_index("player_id")[cols]
    b = short[(short.season == 2025) & (short.week == 8)].set_index("player_id")[cols]
    assert a.notna().all().all()
    pd.testing.assert_frame_equal(a.sort_index(), b.sort_index())


def test_test_season_hidden_unless_asked(league, pred):
    assert TEST_SEASON in set(pred["season"])
    assert TEST_SEASON not in set(predict(league)["season"])


def test_explanation_line_and_long_table(pred):
    r = pred.dropna(subset=["floor"]).iloc[0]
    assert r["explanation"].startswith(f"recent average {r['step_baseline']:.1f} → ")
    assert r["explanation"].endswith(f"median {r['median']:.1f} (floor {r['floor']:.1f}, ceiling {r['ceiling']:.1f})")
    assert pred[pred["step_baseline"].isna()]["explanation"].str.startswith("no projection").all()
    long = explanation_table(pred.head(20))
    assert len(long) == 20 * len(STEPS)
    sums = long.groupby(["player_id", "season", "week"])["delta"].sum(min_count=len(STEPS))
    med = pred.head(20).set_index(["player_id", "season", "week"])["median"]
    np.testing.assert_allclose(sums.reindex(med.index), med, atol=1e-9)


def test_frozen_config_refuses_unimplemented_settings(tmp_path):
    raw = json.loads(CONFIG_PATH.read_text())
    assert load_model()["baseline"] == "ewma_hl8"
    for bad in ({"final_calibration": "ols"}, {"rec": {**raw["rec"], "vacated": True}}):
        p = tmp_path / "params.json"
        p.write_text(json.dumps({**raw, **bad}))
        with pytest.raises(ValueError):
            load_model(p)
