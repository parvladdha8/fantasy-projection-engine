"""Tests for the math. Run with: uv run pytest"""

import numpy as np
import pandas as pd
import pytest

from fantasy_projection_engine.baseline import METHODS, add_projection, big60_pool
from fantasy_projection_engine.metrics import mae, rmse
from fantasy_projection_engine.scoring import ppr_points


def test_mae_rmse_by_hand():
    # misses of 1, 3 -> MAE 2, RMSE sqrt((1+9)/2)=sqrt(5)
    assert mae([10, 20], [11, 17]) == pytest.approx(2.0)
    assert rmse([10, 20], [11, 17]) == pytest.approx(np.sqrt(5))


def test_ppr_scoring_hand_example():
    row = {c: 0 for c in [
        "passing_yards", "passing_tds", "passing_interceptions", "rushing_yards", "rushing_tds",
        "receiving_yards", "receiving_tds", "receptions", "passing_2pt_conversions",
        "rushing_2pt_conversions", "receiving_2pt_conversions", "rushing_fumbles_lost",
        "receiving_fumbles_lost", "sack_fumbles_lost", "special_teams_tds"]}
    # WR: 6 catches, 85 yds, 1 TD, 1 fumble lost -> 6 + 8.5 + 6 - 2 = 18.5
    row.update(receptions=6, receiving_yards=85, receiving_tds=1, receiving_fumbles_lost=1)
    assert ppr_points(pd.DataFrame([row])).iloc[0] == pytest.approx(18.5)


def _toy_games():
    return pd.DataFrame({
        "player_id": ["A"] * 4 + ["B"] * 2,
        "position": ["WR"] * 6,
        "season": [2019] * 6,
        "week": [1, 2, 3, 4, 1, 2],
        "actual": [10.0, 20.0, 30.0, 40.0, 5.0, 7.0],
    })


def test_baseline_values():
    out = add_projection(_toy_games(), "career_mean")
    # Player A: wk1 no history, wk2 = 10, wk3 = 15, wk4 = 20. Player B: NaN, 5.
    assert out["proj"].iloc[0] != out["proj"].iloc[0]  # NaN
    assert list(out["proj"].iloc[1:4]) == [10.0, 15.0, 20.0]
    assert out["proj"].iloc[5] == 5.0


@pytest.mark.parametrize("method", list(METHODS))
def test_no_lookahead(method):
    """Changing week W's actual must not change week W's (or earlier) projection."""
    g = _toy_games()
    before = add_projection(g, method)["proj"]
    g2 = g.copy()
    g2.loc[2, "actual"] = 999.0  # player A, week 3
    after = add_projection(g2, method)["proj"]
    pd.testing.assert_series_equal(before.iloc[:3], after.iloc[:3])  # weeks 1–3 unchanged
    assert after.iloc[3] != before.iloc[3]  # week 4 *should* react
    pd.testing.assert_series_equal(before.iloc[4:], after.iloc[4:])  # other players untouched


def test_big60_pool_uses_projection_not_actual():
    df = pd.DataFrame({
        "season": [2019] * 12, "week": [1] * 12, "position": ["QB"] * 12,
        "proj": list(range(12)),            # highest projections: rows 2..11
        "actual": list(range(12))[::-1],     # highest actuals: rows 0..9
    })
    pool = big60_pool(df)
    assert len(pool) == 10
    assert set(pool.index) == set(range(2, 12))


def test_relevant_pool_slots_and_projection_only():
    from fantasy_projection_engine.baseline import RELEVANT_SLOTS
    df = pd.DataFrame({
        "season": [2019] * 40, "week": [1] * 40, "position": ["RB"] * 40,
        "proj": list(range(40)), "actual": list(range(40))[::-1],
    })
    pool = big60_pool(df, slots=RELEVANT_SLOTS)
    assert len(pool) == 30 and set(pool.index) == set(range(10, 40))
