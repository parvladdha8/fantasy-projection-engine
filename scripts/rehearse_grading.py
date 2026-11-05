"""Rehearsal of live grading on a week that has already been played (local SQLite only; Supabase untouched).

Rebuilds 2026 week W as if it were upcoming (only data from before it), saves it as a run timed before kickoff,
freezes it, then grades it with the real results through the same code the scheduled job uses.
Usage: uv run python scripts/rehearse_grading.py [week]   (default 8). Writes reports/rehearse_grading_week<W>.md
"""

import sys

import pandas as pd

from fantasy_projection_engine import LIVE_SEASON
from fantasy_projection_engine.data import PROJECT_ROOT, latest_live, load_live
from fantasy_projection_engine.live import kickoffs, live_games
from fantasy_projection_engine.predict import predict
from fantasy_projection_engine.storage import connect_sqlite, finish_run, freeze_games, save_projections, start_run

from score_live import grade, read

season, week = LIVE_SEASON, int(sys.argv[1]) if len(sys.argv) > 1 else 8
pull = latest_live(season)
games, _, excluded, src = live_games(season, week=week, pull=pull)
pred = predict(games, allow_test=True)
pred = pred[(pred.season == season) & (pred.week == week)]
k = kickoffs(load_live(season, "schedules", pull), season)
k = k[k.week == week]
run_at = (pd.Timestamp(k.kickoff.min()) - pd.Timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M:%SZ")
c = connect_sqlite()
start_run(c, "rehearsal", data_pull=pull.name, at=run_at)
save_projections(c, "rehearsal", pred)
finish_run(c, "rehearsal", ok=True, at=run_at)
for s, col in [("ours", "median"), ("baseline", "baseline")]:
    freeze_games(c, k[["game_id", "kickoff"]], now="2099-01-01T00:00:00Z", source=s, column=col)
lines = grade(c, season, pull)
inact = read(c, "SELECT reason, COUNT(*) AS n FROM inactive_log GROUP BY reason")
zero = read(c, "SELECT COUNT(*) AS n FROM frozen_projections f LEFT JOIN actuals a USING (player_id, game_id) "
               "LEFT JOIN inactive_log i USING (player_id, game_id) WHERE f.source = 'ours' AND a.player_id IS NULL AND i.player_id IS NULL")
pos = read(c, "SELECT position, n, mae_ours, mae_platform FROM leaderboard_position ORDER BY position")
L = [f"# Grading rehearsal: {season} week {week} (local SQLite; not published)", "",
     f"Projected {len(pred)} players as if week {week} were upcoming (data pull {pull.name}; team from {src}; "
     f"{len(excluded)} left out as designated Out).", ""] + [f"- {l}" for l in lines] + \
    ["", "Inactive log (players with a frozen projection who were inactive at kickoff):", ""] + \
    [f"- {r.reason}: {r.n}" for r in inact.itertuples()] + \
    [f"- active with no stat line (scored 0): {int(zero.n.iloc[0])}", "", "| position | n | MAE ours | MAE baseline |", "|---|---|---|---|"] + \
    [f"| {r.position} | {r.n} | {r.mae_ours:.3f} | {r.mae_platform:.3f} |" for r in pos.itertuples()]
(PROJECT_ROOT / "reports" / f"rehearse_grading_week{week:02d}.md").write_text("\n".join(L) + "\n")
print("\n".join(L))
