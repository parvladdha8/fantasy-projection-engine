"""Tests for platform snapshots: rescoring, matching, and freezing the latest pre-kickoff snapshot."""

import pandas as pd
import pytest

from fantasy_projection_engine.consensus import parse_sleeper, rescore
from fantasy_projection_engine.storage import connect_sqlite, freeze_platform, save_snapshots


def test_rescore_uses_nflverse_rule():
    qb = {"pass_yd": 250, "pass_td": 2, "pass_int": 1, "rush_yd": 20, "fum_lost": 1}
    assert rescore(qb) == pytest.approx(10 + 8 - 2 + 2 - 2)                     # INT and lost fumble both −2
    assert rescore({"rec": 5, "rec_yd": 60, "rec_td": 1, "rec_2pt": 1}) == pytest.approx(5 + 6 + 6 + 2)


def _raw():
    st = {"pts_ppr": 20.0, "pass_yd": 250, "pass_td": 2, "pass_int": 1}
    return [{"player_id": "100", "week": 9, "team": "LAR", "player": {"position": "QB"}, "stats": st},
            {"player_id": "200", "week": 9, "team": "BUF", "player": {"position": "WR"}, "stats": {"pts_ppr": 9.0, "rec": 4}},
            {"player_id": "300", "week": 9, "team": "LAR", "player": {"position": "K"}, "stats": {"pts_ppr": 8.0}},
            {"player_id": "400", "week": 9, "team": "LAR", "player": {"position": "RB"}, "stats": {}}]


def test_parse_maps_ids_teams_and_games():
    sched = pd.DataFrame({"season": [2026], "week": [9], "game_type": ["REG"], "home_team": ["SEA"], "away_team": ["LA"],
                          "game_id": ["2026_09_LA_SEA"]})
    xw = pd.DataFrame({"sleeper_id": [100], "gsis_id": ["00-001"]})
    df, counts = parse_sleeper(_raw(), xw, sched, 2026, 9, "2026-11-05T21:00:00Z")
    assert df["source_player_id"].tolist() == ["100", "200"]                # kicker and empty stat line skipped
    qb = df.iloc[0]
    assert qb.team == "LA" and qb.game_id == "2026_09_LA_SEA" and qb.player_id == "00-001"
    assert qb.projected == pytest.approx(16.0) and qb.projected_platform == 20.0   # rescored vs Sleeper's own number
    assert counts == {"rows": 2, "unmatched_player": 1, "no_game": 1}


def _snap(captured, proj, game="G1"):
    return pd.DataFrame({"source": "sleeper", "source_player_id": ["100"], "player_id": ["p1"], "season": 2026, "week": 9,
                         "position": "QB", "team": "AAA", "game_id": game, "projected": [proj], "projected_platform": [proj],
                         "captured_at": captured})


def test_freeze_platform_uses_latest_snapshot_before_kickoff():
    c = connect_sqlite()
    for cap, p in [("2026-11-08T12:00:00Z", 15.0), ("2026-11-08T17:30:00Z", 17.0), ("2026-11-08T18:30:00Z", 30.0)]:
        save_snapshots(c, _snap(cap, p))
    ko = pd.DataFrame({"game_id": ["G1"], "kickoff": ["2026-11-08T18:00:00Z"]})
    assert freeze_platform(c, ko, "sleeper", now="2026-11-08T17:59:00Z") == 0       # not kicked off
    assert freeze_platform(c, ko, "sleeper", now="2026-11-08T18:40:00Z") == 1       # late run, still pre-kickoff data
    f = pd.read_sql_query("SELECT * FROM frozen_projections", c)
    assert f["projected"].tolist() == [17.0] and f["origin"].tolist() == ["2026-11-08T17:30:00Z"]
    assert f["frozen_at"].tolist() == ["2026-11-08T18:00:00Z"] and f["recorded_at"].tolist() == ["2026-11-08T18:40:00Z"]
    assert freeze_platform(c, ko, "sleeper", now="2026-11-09T00:00:00Z") == 0       # already frozen


def test_no_pre_kickoff_snapshot_means_nothing_frozen():
    c = connect_sqlite()
    save_snapshots(c, _snap("2026-11-08T19:00:00Z", 30.0))
    ko = pd.DataFrame({"game_id": ["G1"], "kickoff": ["2026-11-08T18:00:00Z"]})
    assert freeze_platform(c, ko, "sleeper", now="2026-11-08T20:00:00Z") == 0
