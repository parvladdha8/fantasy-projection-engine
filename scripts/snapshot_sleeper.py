"""Snapshot Sleeper's projections (by RotoWire) for the next week into consensus_snapshots (private; never published).

One API call per run. Uses the schedule and rosters from the refresh's download (same run on GitHub).
Usage: uv run python scripts/snapshot_sleeper.py [--sqlite PATH]
"""

import sys

from fantasy_projection_engine import LIVE_SEASON
from fantasy_projection_engine.alerts import write_failure
from fantasy_projection_engine.consensus import LABEL, fetch_sleeper, parse_sleeper
from fantasy_projection_engine.data import latest_live, load_live
from fantasy_projection_engine.live import next_week
from fantasy_projection_engine.storage import connect_postgres, connect_sqlite, save_snapshots, utc_now


def main(argv):
    season, pull = LIVE_SEASON, latest_live(LIVE_SEASON)
    sched = load_live(season, "schedules", pull)
    week = next_week(sched, season)
    xw = load_live(season, "rosters", pull)[["sleeper_id", "gsis_id"]]
    now = utc_now()
    rows, counts = parse_sleeper(fetch_sleeper(season, week), xw, sched, season, week, captured_at=now)
    conn = connect_sqlite(argv[argv.index("--sqlite") + 1]) if "--sqlite" in argv else connect_postgres()
    n = save_snapshots(conn, rows)
    conn.close()
    print(f"{now}: {LABEL}, week {week}: {n} player projections stored; not matched to an nflverse player: "
          f"{counts['unmatched_player']}; team not playing / no game: {counts['no_game']}")
    if n == 0:
        raise RuntimeError("Sleeper returned no projections; refusing to store an empty snapshot")


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except Exception as e:
        print(write_failure("Sleeper snapshot (projections unaffected)", e))
        raise SystemExit(1)
