"""Tests for betting-line inputs."""

import numpy as np
import pandas as pd
import pytest

from fantasy_projection_engine.betting import build_team_lines, predict_team_volume


def test_implied_points_and_margin():
    sched = pd.DataFrame({"game_id": ["g1"], "season": [2018], "week": [1], "game_type": ["REG"],
                          "home_team": ["BAL"], "away_team": ["BUF"], "spread_line": [7.5], "total_line": [39.0]})
    t = build_team_lines(sched).set_index("team")
    assert t.loc["BAL", "implied"] == pytest.approx(23.25) and t.loc["BAL", "margin"] == 7.5
    assert t.loc["BUF", "implied"] == pytest.approx(15.75) and t.loc["BUF", "margin"] == -7.5
    assert t["implied"].sum() == pytest.approx(39.0)


def _team_games(seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for season in [2018, 2019, 2020]:
        for team in [f"T{i}" for i in range(8)]:
            for week in range(1, 18):
                implied = rng.uniform(15, 30)
                margin = rng.uniform(-10, 10)
                y = 10 + 0.8 * implied - 0.3 * margin + rng.normal(0, 3)
                rows.append({"team": team, "season": season, "week": week, "vol": y, "implied": implied, "margin": margin})
    return pd.DataFrame(rows).sample(frac=1, random_state=1).reset_index(drop=True)  # shuffled on purpose


def test_line_regression_uses_only_earlier_seasons():
    tg = _team_games()
    before = predict_team_volume(tg, "vol", 8)
    tg2 = tg.copy()
    tg2.loc[tg2["season"] == 2020, "vol"] += 50   # change the LAST season's outcomes
    after = predict_team_volume(tg2, "vol", 8)
    early = (tg["season"] < 2020).to_numpy()
    np.testing.assert_allclose(before[early], after[early], equal_nan=True)
    # season 2020 week 1 uses no 2020 outcomes at all (coefficients from 2018–19, history from 2019)
    wk1 = ((tg["season"] == 2020) & (tg["week"] == 1)).to_numpy()
    np.testing.assert_allclose(before[wk1], after[wk1])


def test_line_regression_recovers_signal():
    tg = _team_games()
    pred = predict_team_volume(tg, "vol", 8)
    s20 = (tg["season"] == 2020).to_numpy()
    truth = 10 + 0.8 * tg["implied"] - 0.3 * tg["margin"]
    assert np.corrcoef(pred[s20], truth[s20])[0, 1] > 0.95


def test_history_only_regression_ignores_lines():
    tg = _team_games()
    a = predict_team_volume(tg, "vol", 8, use_lines=False)
    tg2 = tg.copy()
    tg2["implied"] = 0.0
    tg2["margin"] = 0.0
    b = predict_team_volume(tg2, "vol", 8, use_lines=False)
    np.testing.assert_allclose(a, b, equal_nan=True)
