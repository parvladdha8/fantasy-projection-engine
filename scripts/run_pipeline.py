"""One live refresh: download → project the next week → save to the database as a run → read back and verify.

Usage:
  uv run python scripts/run_pipeline.py            # Supabase (SUPABASE_DB_URL from .env or GitHub Secrets)
  uv run python scripts/run_pipeline.py --local    # local SQLite file db/local.sqlite (for testing)
  add --no-pull to reuse the latest complete download instead of downloading again

Safety: the run is recorded as 'running' first and only marked 'ok' after its projections are saved and checked.
If anything fails, it is marked 'failed' with the error, and the site keeps showing the last ok run.
"""

import subprocess
import sys

import numpy as np

from fantasy_projection_engine import LIVE_SEASON
from fantasy_projection_engine.alerts import write_failure
from fantasy_projection_engine.data import PROJECT_ROOT, latest_live, pull_live, verify_frozen
from fantasy_projection_engine.live import live_games
from fantasy_projection_engine.predict import predict
from fantasy_projection_engine.storage import (PROJ_COLS, connect_postgres, connect_sqlite, finish_run,
                                                latest_ok_projections, save_projections, start_run, utc_now)


def code_version() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                              cwd=PROJECT_ROOT).stdout.strip() or "unknown"
    except OSError:
        return "unknown"


def main(argv):
    local, pull_new = "--local" in argv, "--no-pull" not in argv
    season = LIVE_SEASON
    verify_frozen()  # the frozen 2018–25 data must be byte-for-byte what the model was tested on
    pull = pull_live(season) if pull_new else latest_live(season)
    conn = connect_sqlite(PROJECT_ROOT / "db" / "local.sqlite") if local else connect_postgres()
    run_id = f"run-{utc_now()}"
    start_run(conn, run_id, data_pull=pull.name, code_version=code_version())
    try:
        games, week, excluded, src = live_games(season, pull=pull)
        pred = predict(games, allow_test=True)
        pred = pred[(pred.season == season) & (pred.week == week)].copy()
        if len(pred) < 100 or pred["median"].notna().sum() < 100:
            raise RuntimeError(f"only {len(pred)} players projected for week {week}; refusing to publish a suspiciously small run")
        save_projections(conn, run_id, pred)
        # Read back and compare before marking the run ok.
        stored = conn.execute(*(("SELECT COUNT(*) FROM projections WHERE run_id = ?", (run_id,)) if local else
                                ("SELECT COUNT(*) FROM projections WHERE run_id = %s", (run_id,)))).fetchone()[0]
        if stored != len(pred):
            raise RuntimeError(f"saved {len(pred)} rows but read back {stored}")
        finish_run(conn, run_id, ok=True)
    except Exception as e:
        conn.rollback()
        finish_run(conn, run_id, ok=False, error=f"{type(e).__name__}: {e}"[:2000])
        print(f"RUN FAILED ({run_id}): {type(e).__name__}: {e}\nThe last good projections are still the ones served.")
        raise

    # Independent check: what the site would serve now = this run, identical to what we computed.
    served = latest_ok_projections(conn)
    a = pred.rename(columns={"player_display_name": "player_name", "step_baseline": "baseline"}).set_index(["player_id", "game_id"])
    b = served.set_index(["player_id", "game_id"]).loc[a.index]
    num = ["median", "floor", "ceiling", "baseline"]
    max_diff = np.nanmax(np.abs(a[num].to_numpy(float) - b[num].to_numpy(float)))
    same_text = (a[["player_name", "position", "team", "explanation"]].fillna("") ==
                 b[["player_name", "position", "team", "explanation"]].fillna("")).all().all()
    print(f"run {run_id}  (data pull {pull.name}, code {code_version()})  →  {'local SQLite' if local else 'Supabase'}")
    print(f"week {week}: {len(pred)} players saved; {len(excluded)} left out (designated Out); team from: {src}")
    print(f"served run = this run: {served['run_id'].iloc[0] == run_id};  rows served: {len(served)}")
    print(f"read-back check: largest numeric difference {max_diff:.2e}; names/teams/explanations identical: {same_text}")
    conn.close()


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except Exception as e:  # anything, including failures before the run was recorded (download, database connection)
        print(write_failure("refresh (download → project → save)", e))
        raise SystemExit(1)
