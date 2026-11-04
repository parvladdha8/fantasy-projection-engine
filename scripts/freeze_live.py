"""Kickoff freeze: for every game that has kicked off and isn't frozen yet, copy the projection in effect at kickoff
(the latest ok run that STARTED before kickoff) into frozen_projections, for both our median and the baseline.

Safe to run late or repeatedly: already-frozen games are skipped, and a late run still copies only pre-kickoff runs.
Usage: uv run python scripts/freeze_live.py [--local]
"""

import sys

import nflreadpy as nfl
import pandas as pd

from fantasy_projection_engine import LIVE_SEASON
from fantasy_projection_engine.alerts import write_failure
from fantasy_projection_engine.data import PROJECT_ROOT
from fantasy_projection_engine.live import kickoffs
from fantasy_projection_engine.storage import connect_postgres, connect_sqlite, freeze_games, utc_now


def main(argv):
    local = "--local" in argv
    schedules = nfl.load_schedules([LIVE_SEASON]).to_pandas()   # small download: kickoff times only
    k = kickoffs(schedules, LIVE_SEASON)
    now = utc_now()
    # Only games from the last 14 days: older games were frozen (or had no pre-kickoff run, e.g. before we went live).
    cutoff = (pd.Timestamp(now) - pd.Timedelta(days=14)).strftime("%Y-%m-%dT%H:%M:%SZ")
    k = k[k["kickoff"] >= cutoff]
    conn = connect_sqlite(PROJECT_ROOT / "db" / "local.sqlite") if local else connect_postgres()
    n = {src: freeze_games(conn, k[["game_id", "kickoff"]], now=now, source=src, column=col)
         for src, col in [("ours", "median"), ("baseline", "baseline")]}
    started = k[k["kickoff"] <= now]
    print(f"{now}: {len(started)} games kicked off in the last 14 days; newly frozen rows: ours {n['ours']}, baseline {n['baseline']}")
    conn.close()


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except Exception as e:
        print(write_failure("kickoff freeze", e))
        raise SystemExit(1)
