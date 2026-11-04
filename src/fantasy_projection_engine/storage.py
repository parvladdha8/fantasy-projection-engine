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
             "baseline", "explanation"]


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
    rows = [tuple(None if pd.isna(v) else (v.item() if hasattr(v, "item") else v) for v in r)
            for r in p[PROJ_COLS].itertuples(index=False)]
    conn.executemany(_sql(conn, f"INSERT INTO projections (run_id, {', '.join(PROJ_COLS)}) VALUES ({', '.join('?' * (len(PROJ_COLS) + 1))})"),
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
    n = 0
    for g in kickoffs.itertuples():
        if g.kickoff > now or g.game_id in done:
            continue
        p = latest_ok_projections(conn, before=g.kickoff)
        p = p[(p["game_id"] == g.game_id) & p[column].notna()]
        if column != "median":  # floor/ceiling belong to our median only
            p = p.assign(floor=float("nan"), ceiling=float("nan"))
        conn.executemany(_sql(conn, "INSERT INTO frozen_projections (source, player_id, game_id, season, week, position, team, "
                                    "projected, floor, ceiling, kickoff, frozen_at, origin) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"),
                         [(source, r.player_id, r.game_id, int(r.season), int(r.week), r.position, r.team, float(getattr(r, column)),
                           None if pd.isna(r.floor) else float(r.floor), None if pd.isna(r.ceiling) else float(r.ceiling),
                           g.kickoff, min(now, g.kickoff), r.run_id) for r in p.itertuples()])
        n += len(p)
    conn.commit()
    return n
