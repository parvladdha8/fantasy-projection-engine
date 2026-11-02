"""Tests for snap-count zero games and the paired bootstrap."""

import numpy as np
import pandas as pd
import pytest

from fantasy_projection_engine.baseline import add_projection, prepare_games
from fantasy_projection_engine.metrics import paired_bootstrap
from fantasy_projection_engine.player_games import build_player_games


def _toy_sources():
    ps = pd.DataFrame({
        "player_id": ["G1", "G1"], "player_display_name": ["Al"] * 2, "position": ["TE"] * 2,
        "team": ["KC"] * 2, "season": [2019] * 2, "week": [1, 3], "season_type": ["REG"] * 2,
        "game_id": ["2019_01_KC_X", "2019_03_KC_Y"], "fantasy_points_ppr": [10.0, 20.0],
    })
    snaps = pd.DataFrame({
        "game_id": ["2019_01_KC_X", "2019_02_KC_Z", "2019_03_KC_Y", "2019_04_KC_W"],
        "game_type": ["REG"] * 4, "season": [2019] * 4, "week": [1, 2, 3, 4],
        "pfr_player_id": ["P1"] * 4, "team": ["KC"] * 4,
        "position": ["FB"] * 4,                    # PFR label differs: must be ignored
        "offense_snaps": [30.0, 25.0, 40.0, 0.0],  # week 4: special teams only -> no row
        "offense_pct": [0.5, 0.4, 0.6, 0.0],
    })
    players = pd.DataFrame({"gsis_id": ["G1"], "pfr_id": ["P1"], "display_name": ["Al"], "position": ["TE"]})
    return ps, snaps, players


def test_snap_only_game_becomes_zero_row():
    pg = build_player_games(*_toy_sources())
    assert list(pg["week"]) == [1, 2, 3]  # week 2 added, week 4 (0 offense snaps) not
    wk2 = pg[pg["week"] == 2].iloc[0]
    assert wk2["fantasy_points_ppr"] == 0.0 and wk2["source"] == "snaps_only"
    assert set(pg["position"]) == {"TE"}  # nflverse position, not PFR's "FB"


def test_zero_games_in_history_only_when_enabled():
    pg = build_player_games(*_toy_sources())
    new = add_projection(prepare_games(pg, True), "career_mean")
    old = add_projection(prepare_games(pg, False), "career_mean")
    # week 3 projection: new = mean(10, 0) = 5; old skips the zero -> 10
    assert new.loc[new["week"] == 3, "proj"].iat[0] == pytest.approx(5.0)
    assert old.loc[old["week"] == 3, "proj"].iat[0] == pytest.approx(10.0)
    # but the zero game is still SCORED in both versions
    assert (old["week"] == 2).any() and old.loc[old["week"] == 2, "actual"].iat[0] == 0.0


def test_paired_bootstrap_detects_clear_winner():
    rng = np.random.default_rng(1)
    eb = rng.uniform(4, 8, 2000)
    ea = eb - 0.5                       # A always 0.5 better
    clusters = np.repeat(np.arange(100), 20)
    r = paired_bootstrap(ea, eb, clusters)
    assert r["diff"] == pytest.approx(-0.5)
    assert r["ci_high"] < 0 and r["p_a_not_better"] == 0.0


def test_paired_bootstrap_no_difference():
    rng = np.random.default_rng(2)
    eb = rng.uniform(4, 8, 2000)
    ea = eb + rng.normal(0, 1, 2000)    # pure noise, no true edge
    r = paired_bootstrap(ea - (ea - eb).mean(), eb, np.repeat(np.arange(100), 20))
    assert r["ci_low"] < 0 < r["ci_high"]
