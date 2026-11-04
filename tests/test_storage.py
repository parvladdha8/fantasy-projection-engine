"""Tests for storage: runs, living projections, kickoff freezes, immutability (SQLite in memory)."""

import sqlite3

import pandas as pd
import pytest

from fantasy_projection_engine.storage import (connect_sqlite, finish_run, freeze_games, latest_ok_projections,
                                               save_projections, start_run)


def _proj(median, game="G1", pid="p1"):
    return pd.DataFrame({"player_id": [pid], "game_id": [game], "season": [2026], "week": [9], "player_display_name": ["X"],
                         "position": ["WR"], "team": ["AAA"], "median": [median], "floor": [2.0], "ceiling": [30.0],
                         "explanation": ["..."]})


def _run(conn, rid, at, median, ok=True, game="G1"):
    start_run(conn, rid, at=at)
    save_projections(conn, rid, _proj(median, game))
    finish_run(conn, rid, ok=ok, at=at, error=None if ok else "source down")


def test_failed_run_never_replaces_last_good():
    c = connect_sqlite()
    _run(c, "r1", "2026-11-05T10:00:00Z", 12.0)
    _run(c, "r2", "2026-11-05T13:00:00Z", 99.0, ok=False)
    assert latest_ok_projections(c)["median"].tolist() == [12.0]


def test_freeze_uses_last_ok_run_started_before_kickoff():
    c = connect_sqlite()
    _run(c, "r1", "2026-11-08T12:00:00Z", 12.0)
    _run(c, "r2", "2026-11-08T17:00:00Z", 14.0)
    _run(c, "r3", "2026-11-08T19:00:00Z", 50.0)   # after kickoff: must not count
    ko = pd.DataFrame({"game_id": ["G1"], "kickoff": ["2026-11-08T18:00:00Z"]})
    assert freeze_games(c, ko, now="2026-11-08T17:30:00Z") == 0      # not kicked off yet
    assert freeze_games(c, ko, now="2026-11-08T20:00:00Z") == 1
    f = pd.read_sql_query("SELECT * FROM frozen_projections", c)
    assert f["projected"].tolist() == [14.0] and f["origin"].tolist() == ["r2"]
    assert (f["frozen_at"] <= f["kickoff"]).all()
    assert freeze_games(c, ko, now="2026-11-09T20:00:00Z") == 0      # already frozen: skipped


def test_frozen_rows_cannot_be_changed_or_backdated():
    c = connect_sqlite()
    _run(c, "r1", "2026-11-08T12:00:00Z", 12.0)
    freeze_games(c, pd.DataFrame({"game_id": ["G1"], "kickoff": ["2026-11-08T18:00:00Z"]}), now="2026-11-08T20:00:00Z")
    with pytest.raises(sqlite3.DatabaseError, match="immutable"):
        c.execute("UPDATE frozen_projections SET projected = 20")
    with pytest.raises(sqlite3.DatabaseError, match="immutable"):
        c.execute("DELETE FROM frozen_projections")
    with pytest.raises(sqlite3.IntegrityError):  # a freeze stamped after kickoff is refused by the CHECK
        c.execute("INSERT INTO frozen_projections (source, player_id, game_id, season, week, position, projected, kickoff, frozen_at) "
                  "VALUES ('ours', 'p2', 'G1', 2026, 9, 'WR', 5, '2026-11-08T18:00:00Z', '2026-11-08T18:05:00Z')")


def test_postgres_files_exist_and_name_the_trigger():
    from fantasy_projection_engine.storage import DB_DIR
    assert "frozen_projections" in (DB_DIR / "immutable_postgres.sql").read_text()


def test_one_run_freezes_ours_and_baseline_together():
    c = connect_sqlite()
    start_run(c, "r1", at="2026-11-08T12:00:00Z")
    save_projections(c, "r1", _proj(12.0).assign(step_baseline=10.0))
    finish_run(c, "r1", ok=True, at="2026-11-08T12:00:00Z")
    ko = pd.DataFrame({"game_id": ["G1"], "kickoff": ["2026-11-08T18:00:00Z"]})
    freeze_games(c, ko, now="2026-11-08T20:00:00Z", source="ours", column="median")
    freeze_games(c, ko, now="2026-11-08T20:00:00Z", source="baseline", column="baseline")
    f = pd.read_sql_query("SELECT source, projected, floor FROM frozen_projections ORDER BY source", c)
    assert f["projected"].tolist() == [10.0, 12.0] and pd.isna(f["floor"].iloc[0]) and f["floor"].iloc[1] == 2.0


def test_parse_db_url_special_characters():
    from fantasy_projection_engine.storage import parse_db_url
    c = parse_db_url("postgresql://postgres.abc:p@ss:w#rd@aws-0-us-east-1.pooler.supabase.com:5432/postgres")
    assert c == {"user": "postgres.abc", "password": "p@ss:w#rd", "host": "aws-0-us-east-1.pooler.supabase.com",
                 "port": 5432, "dbname": "postgres"}
