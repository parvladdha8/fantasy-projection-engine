"""Tests for live (upcoming-game) rows: who gets a row, and that outcomes stay blank."""

import numpy as np
import pandas as pd

from fantasy_projection_engine.live import OUTCOME_COLS, candidates, out_designations


def _pg():
    r = lambda pid, team, s, w: {"player_id": pid, "player_display_name": pid, "position": "WR", "team": team,
                                  "season": s, "week": w, "game_id": f"{s}_{w}"}
    return pd.DataFrame([r("stay", "AAA", 2026, 1), r("stay", "AAA", 2026, 2),
                         r("traded", "AAA", 2026, 1), r("traded", "BBB", 2026, 2),
                         r("lastyear_only", "AAA", 2025, 17),
                         r("bye_team", "CCC", 2026, 2),
                         r("future", "AAA", 2026, 3)])  # week-3 row must never be used for week 3


def _sch(season=2026, week=3):
    return pd.DataFrame({"game_type": ["REG"], "season": [season], "week": [week], "game_id": [f"{season}_{week}_AAA_BBB"],
                         "home_team": ["BBB"], "away_team": ["AAA"]})


def test_candidates_follow_most_recent_team_and_skip_byes():
    c = candidates(_pg(), _sch(), 2026, 3).set_index("player_id")
    assert c.loc["stay", "team"] == "AAA" and c.loc["traded", "team"] == "BBB"  # traded player moves with his new team
    assert "lastyear_only" not in c.index      # hasn't played this season
    assert "bye_team" not in c.index           # team not playing this week
    assert "future" not in c.index             # only rows BEFORE the week count
    assert c[OUTCOME_COLS].isna().all().all() and (c["source"] == "upcoming").all()


def test_week1_uses_last_season_team():
    pg = pd.DataFrame({"player_id": ["a", "b"], "player_display_name": ["a", "b"], "position": "RB",
                       "team": ["AAA", "CCC"], "season": 2025, "week": 18, "game_id": "x"})
    c = candidates(pg, _sch(2026, 1), 2026, 1)
    assert c["player_id"].tolist() == ["a"]


def test_out_designations():
    inj = pd.DataFrame({"season": 2026, "week": 3, "game_type": "REG", "gsis_id": ["p1", "p2", "p3"],
                        "report_status": ["Out", "Questionable", np.nan]})
    assert out_designations(inj, 2026, 3)["player_id"].tolist() == ["p1"]
    assert out_designations(inj, 2026, 4).empty


def test_roster_overrides_team_and_drops_reserve():
    roster = pd.DataFrame({"player_id": ["stay", "traded", "signed"], "team": ["BBB", "AAA", "AAA"],
                           "status": ["ACT", "RES", "ACT"]})
    pg = _pg()
    c = candidates(pg, _sch(), 2026, 3, roster).set_index("player_id")
    assert c.loc["stay", "team"] == "BBB"          # roster move beats last-game team
    assert "traded" not in c.index                 # on reserve → excluded
    assert "signed" not in c.index                 # no game history → nothing to project from
    assert "bye_team" not in c.index


def test_roster_week1_offseason_mover():
    pg = pd.DataFrame({"player_id": ["mover"], "player_display_name": ["mover"], "position": "WR",
                       "team": ["CCC"], "season": 2025, "week": 18, "game_id": "x"})
    roster = pd.DataFrame({"player_id": ["mover"], "team": ["AAA"], "status": ["ACT"]})
    c = candidates(pg, _sch(2026, 1), 2026, 1, roster)
    assert c["team"].tolist() == ["AAA"]           # offseason signing is placed on his new team


def test_kickoffs_convert_eastern_to_utc_across_daylight_saving():
    from fantasy_projection_engine.live import kickoffs
    s = pd.DataFrame({"game_id": ["a", "b", "c"], "season": 2026, "week": [8, 9, 1], "game_type": ["REG", "REG", "POST"],
                      "gameday": ["2026-10-25", "2026-11-08", "2027-01-10"], "gametime": ["13:00", "13:00", "16:30"]})
    k = kickoffs(s, 2026)
    assert k["kickoff"].tolist() == ["2026-10-25T17:00:00Z", "2026-11-08T18:00:00Z"]   # EDT (−4) then EST (−5); playoffs left out
