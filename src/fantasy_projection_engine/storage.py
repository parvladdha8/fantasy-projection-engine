"""Storage: runs, living projections, kickoff freezes. Schema in db/schema.sql (DECISIONS.md, 2026-11-04).

Written against Python's DB-API so the same code serves SQLite (local tests, file on this laptop) and, later,
Postgres on Supabase. Placeholders are written as '?' and converted for Postgres.
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .data import PROJECT_ROOT

DB_DIR = PROJECT_ROOT / "db"
PROJ_COLS = ["player_id", "game_id", "season", "week", "player_name", "position", "team", "median", "floor", "ceiling",
             "baseline", "explanation", "injury_status", "p_play"]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sql(conn, q: str) -> str:
    return q if isinstance(conn, sqlite3.Connection) else q.replace("?", "%s")


def connect_sqlite(path: str | Path = ":memory:") -> sqlite3.Connection:
    """Local database with the full schema, including the immutability triggers."""
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript((DB_DIR / "schema.sql").read_text())
    conn.executescript((DB_DIR / "immutable_sqlite.sql").read_text())
    return conn


def parse_db_url(url: str) -> dict:
    """Split a postgresql:// URL into connection settings, tolerating special characters in the password.

    Supabase passwords may contain '@', ':' etc., which break normal URL parsing unless percent-encoded.
    The host comes after the LAST '@'; the user is before the FIRST ':' of what precedes it.
    """
    rest = url.strip().split("://", 1)[1]
    userinfo, _, hostpart = rest.rpartition("@")
    user, _, password = userinfo.partition(":")
    hostport, _, dbname = hostpart.partition("/")
    host, _, port = hostport.partition(":")
    return {"user": user, "password": password, "host": host, "port": int(port or 5432),
            "dbname": dbname.split("?", 1)[0] or "postgres"}


def read_env(name: str, path: Path = PROJECT_ROOT / ".env") -> str | None:
    """Value of NAME from the environment (GitHub Secrets) or, failing that, the local git-ignored .env file."""
    import os
    if os.environ.get(name):
        return os.environ[name]
    if path.exists():
        for line in path.read_text().splitlines():
            if line.startswith(name + "="):
                return line.split("=", 1)[1].strip()
    return None


def connect_postgres(url: str | None = None):
    """Connection to Supabase Postgres. The password is never printed or logged."""
    import psycopg
    url = url or read_env("SUPABASE_DB_URL")
    if not url:
        raise RuntimeError("SUPABASE_DB_URL is not set (in .env locally, or as a GitHub Secret).")
    return psycopg.connect(**parse_db_url(url), sslmode="require", connect_timeout=15)


def start_run(conn, run_id: str, data_pull: str | None = None, code_version: str | None = None, at: str | None = None):
    conn.execute(_sql(conn, "INSERT INTO runs (run_id, started_at, status, data_pull, code_version) VALUES (?, ?, 'running', ?, ?)"),
                 (run_id, at or utc_now(), data_pull, code_version))
    conn.commit()


def finish_run(conn, run_id: str, ok: bool, error: str | None = None, at: str | None = None):
    conn.execute(_sql(conn, "UPDATE runs SET status = ?, finished_at = ?, error = ? WHERE run_id = ?"),
                 ("ok" if ok else "failed", at or utc_now(), error, run_id))
    conn.commit()


def save_projections(conn, run_id: str, proj: pd.DataFrame):
    """Store one run's projections (columns PROJ_COLS; extra columns ignored)."""
    p = proj.rename(columns={"player_display_name": "player_name", "step_baseline": "baseline"})
    if "baseline" not in p:
        p = p.assign(baseline=float("nan"))
    for c in ("injury_status", "p_play"):      # optional: healthy players / callers without injury data
        if c not in p:
            p = p.assign(**{c: None})
    rows = [tuple(None if pd.isna(v) else (v.item() if hasattr(v, "item") else v) for v in r)
            for r in p[PROJ_COLS].itertuples(index=False)]
    conn.cursor().executemany(_sql(conn, f"INSERT INTO projections (run_id, {', '.join(PROJ_COLS)}) VALUES ({', '.join('?' * (len(PROJ_COLS) + 1))})"),
                     [(run_id, *r) for r in rows])
    conn.commit()


def latest_ok_projections(conn, before: str | None = None) -> pd.DataFrame:
    """Projections of the most recent run with status 'ok' (that started before `before`, if given).
    Failed or still-running runs are never used, so a failed run can't replace the last good projections."""
    q = "SELECT run_id, started_at FROM runs WHERE status = 'ok'" + (" AND started_at < ?" if before else "") + \
        " ORDER BY started_at DESC LIMIT 1"
    r = conn.execute(_sql(conn, q), (before,) if before else ()).fetchone()
    if r is None:
        return pd.DataFrame(columns=["run_id", "run_started_at", *PROJ_COLS])
    df = pd.read_sql_query(_sql(conn, "SELECT * FROM projections WHERE run_id = ?"), conn, params=(r[0],))
    return df.assign(run_started_at=r[1])


def freeze_games(conn, kickoffs: pd.DataFrame, now: str | None = None, source: str = "ours", column: str = "median") -> int:
    """Freeze every game whose kickoff has passed and that isn't frozen yet for `source`: copy the latest ok
    projection from a run that STARTED before that game's kickoff. kickoffs: game_id, kickoff (UTC ISO).
    Returns the number of player rows frozen. Already-frozen games are skipped (the table is immutable)."""
    now = now or utc_now()
    done = {r[0] for r in conn.execute(_sql(conn, "SELECT DISTINCT game_id FROM frozen_projections WHERE source = ?"), (source,))}
    n, cache = 0, {}
    for g in kickoffs.itertuples():
        if g.kickoff > now or g.game_id in done:
            continue
        if g.kickoff not in cache:  # games sharing a kickoff time (e.g. Sunday 1 pm) share one lookup
            cache[g.kickoff] = latest_ok_projections(conn, before=g.kickoff)
        p = cache[g.kickoff]
        p = p[(p["game_id"] == g.game_id) & p[column].notna()]
        if column != "median":  # floor/ceiling belong to our median only
            p = p.assign(floor=float("nan"), ceiling=float("nan"))
        conn.cursor().executemany(_sql(conn, "INSERT INTO frozen_projections (source, player_id, game_id, season, week, position, team, "
                                    "projected, floor, ceiling, kickoff, frozen_at, origin, recorded_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"),
                         [(source, r.player_id, r.game_id, int(r.season), int(r.week), r.position, r.team, float(getattr(r, column)),
                           None if pd.isna(r.floor) else float(r.floor), None if pd.isna(r.ceiling) else float(r.ceiling),
                           g.kickoff, min(now, g.kickoff), r.run_id, now) for r in p.itertuples()])
        n += len(p)
    conn.commit()
    return n


def save_grading(conn, season: int, week: int, actuals: pd.DataFrame, inactive: pd.DataFrame, weekly: list[dict],
                 positions: pd.DataFrame, now: str | None = None, highlights: pd.DataFrame | None = None):
    """Replace one week's actuals, inactive log and leaderboard rows in a single transaction (re-scoring for stat
    corrections overwrites the provisional result; nothing is half-written if it fails). Frozen projections are untouched."""
    now = now or utc_now()
    cur = conn.cursor()
    try:
        for t in ("actuals", "inactive_log", "leaderboard_weekly", "leaderboard_position", "leaderboard_highlights"):
            cur.execute(_sql(conn, f"DELETE FROM {t} WHERE season = ? AND week = ?"), (season, week))
        cur.executemany(_sql(conn, "INSERT INTO actuals (player_id, game_id, season, week, points_ppr, ingested_at) VALUES (?, ?, ?, ?, ?, ?)"),
                        [(r.player_id, r.game_id, season, week, float(r.points_ppr), now) for r in actuals.itertuples()])
        cur.executemany(_sql(conn, "INSERT INTO inactive_log (player_id, game_id, season, week, reason, logged_at) VALUES (?, ?, ?, ?, ?, ?)"),
                        [(r.player_id, r.game_id, season, week, r.reason, now) for r in inactive.itertuples()])
        cols = ["platform", "n_pool", "n_scored", "n_dropped_no_ours", "n_inactive", "mae_ours", "mae_platform", "rmse_ours",
                "rmse_platform", "spearman_ours", "spearman_platform", "winner"]
        cur.executemany(_sql(conn, f"INSERT INTO leaderboard_weekly (season, week, {', '.join(cols)}, computed_at) "
                                   f"VALUES (?, ?, {', '.join('?' * len(cols))}, ?)"),
                        [(season, week, *[None if isinstance(w[c], float) and pd.isna(w[c]) else
                                          (w[c].item() if hasattr(w[c], "item") else w[c]) for c in cols], now) for w in weekly])
        cur.executemany(_sql(conn, "INSERT INTO leaderboard_position (platform, season, week, position, n, mae_ours, mae_platform) "
                                   "VALUES (?, ?, ?, ?, ?, ?, ?)"),
                        [(r.platform, season, week, r.position, int(r.n), float(r.mae_ours), float(r.mae_platform))
                         for r in positions.itertuples()])
        if highlights is not None and len(highlights):
            cur.executemany(_sql(conn, "INSERT INTO leaderboard_highlights (platform, season, week, kind, rank, player_id, player_name, position) "
                                       "VALUES (?, ?, ?, ?, ?, ?, ?, ?)"),
                            [(r.platform, season, week, r.kind, int(r.rank), r.player_id, r.player_name, r.position)
                             for r in highlights.itertuples()])
        conn.commit()
    except Exception:
        conn.rollback()
        raise


WEATHER_COLS = ["game_id", "fetched_at", "kickoff", "stadium_id", "roof", "latitude", "longitude", "temp_f", "wind_mph",
                "gust_mph", "precip_mm", "precip_prob", "snow_cm", "source"]


def save_weather(conn, rows: pd.DataFrame) -> int:
    """Append one fetch's forecasts (never overwrites earlier fetches)."""
    if rows.empty:
        return 0
    vals = [tuple(None if pd.isna(v) else (v.item() if hasattr(v, "item") else v) for v in r)
            for r in rows[WEATHER_COLS].itertuples(index=False)]
    conn.cursor().executemany(_sql(conn, f"INSERT INTO weather_forecasts ({', '.join(WEATHER_COLS)}) VALUES "
                                         f"({', '.join('?' * len(WEATHER_COLS))})"), vals)
    conn.commit()
    return len(vals)


SNAP_COLS = ["source", "source_player_id", "player_id", "season", "week", "position", "team", "game_id", "projected",
             "projected_platform", "captured_at"]


def save_snapshots(conn, rows: pd.DataFrame) -> int:
    """Append one platform snapshot (every capture kept)."""
    if rows.empty:
        return 0
    vals = [tuple(None if pd.isna(v) else (v.item() if hasattr(v, "item") else v) for v in r)
            for r in rows[SNAP_COLS].itertuples(index=False)]
    conn.cursor().executemany(_sql(conn, f"INSERT INTO consensus_snapshots ({', '.join(SNAP_COLS)}) VALUES "
                                         f"({', '.join('?' * len(SNAP_COLS))})"), vals)
    conn.commit()
    return len(vals)


def freeze_platform(conn, kickoffs: pd.DataFrame, source: str, now: str | None = None) -> int:
    """Freeze a platform for every game that has kicked off and isn't frozen yet for it: each matched player's projection
    from the platform's latest snapshot CAPTURED BEFORE that game's kickoff. Same immutability rules as ours."""
    now = now or utc_now()
    done = {r[0] for r in conn.execute(_sql(conn, "SELECT DISTINCT game_id FROM frozen_projections WHERE source = ?"), (source,))}
    n = 0
    for g in kickoffs.itertuples():
        if g.kickoff > now or g.game_id in done:
            continue
        cur = conn.cursor()
        cur.execute(_sql(conn, "SELECT MAX(captured_at) FROM consensus_snapshots WHERE source = ? AND game_id = ? AND captured_at < ?"),
                    (source, g.game_id, g.kickoff))
        cap = cur.fetchone()[0]
        if cap is None:
            continue
        cur.execute(_sql(conn, "SELECT player_id, season, week, position, team, projected FROM consensus_snapshots "
                               "WHERE source = ? AND game_id = ? AND captured_at = ? AND player_id IS NOT NULL AND projected IS NOT NULL"),
                    (source, g.game_id, cap))
        rows = list({r[0]: r for r in cur.fetchall()}.values())   # one row per player (two platform ids can map to one player)
        conn.cursor().executemany(_sql(conn, "INSERT INTO frozen_projections (source, player_id, game_id, season, week, position, "
                                             "team, projected, floor, ceiling, kickoff, frozen_at, origin, recorded_at) "
                                             "VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?, ?, ?)"),
                                  [(source, r[0], g.game_id, int(r[1]), int(r[2]), r[3], r[4], float(r[5]), g.kickoff,
                                    min(now, g.kickoff), cap, now) for r in rows])
        n += len(rows)
    conn.commit()
    return n
