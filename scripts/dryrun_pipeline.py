"""End-to-end dry run of storage + Big 60 on a past season (SQLite in memory; nothing published).

For each week: a run saves our medians and the baseline's projections, the database freezes each game at
kickoff, actual points are ingested, and the Big 60 is scored with the baseline as the platform.
On 2025 it must reproduce the one-time test's weekly head-to-head (16–2) exactly. Plumbing check only: nothing is tuned.

Usage: uv run python scripts/dryrun_pipeline.py [season]
"""

import sys

import pandas as pd

from fantasy_projection_engine.data import PROJECT_ROOT, load_schedules
from fantasy_projection_engine.leaderboard import score_week, season_record
from fantasy_projection_engine.predict import load_games, predict
from fantasy_projection_engine.storage import connect_sqlite, finish_run, freeze_games, save_projections, start_run

season = int(sys.argv[1]) if len(sys.argv) > 1 else 2025
sch = load_schedules()
sch = sch[(sch.game_type == "REG") & (sch.season == season)].copy()
ko = pd.to_datetime(sch.gameday + " " + sch.gametime).dt.tz_localize("America/New_York").dt.tz_convert("UTC")
sch["kickoff"] = ko.dt.strftime("%Y-%m-%dT%H:%M:%SZ")
pred = predict(load_games(), allow_test=True)
pred = pred[pred.season == season].dropna(subset=["median", "step_baseline"])

c = connect_sqlite()
weekly = []
for w in sorted(pred.week.unique()):
    p = pred[pred.week == w]
    k = sch[sch.week == w]
    run_at = (pd.Timestamp(k.kickoff.min()) - pd.Timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M:%SZ")
    rid = f"run-{season}-{w:02d}"
    start_run(c, rid, at=run_at)
    save_projections(c, rid, p)           # one run stores our median/floor/ceiling AND the baseline
    finish_run(c, rid, ok=True, at=run_at)
    for src, col in [("ours", "median"), ("baseline", "baseline")]:
        freeze_games(c, k[["game_id", "kickoff"]], now="2099-01-01T00:00:00Z", source=src, column=col)
    c.executemany("INSERT INTO actuals VALUES (?, ?, ?, ?, ?, ?)",
                  [(r.player_id, r.game_id, season, int(w), float(r.actual), "2099-01-01T00:00:00Z") for r in p.itertuples()])
    f = pd.read_sql_query("SELECT * FROM frozen_projections WHERE season = ? AND week = ?", c, params=(season, int(w)))
    act = pd.read_sql_query("SELECT * FROM actuals WHERE season = ? AND week = ?", c, params=(season, int(w)))
    row, _, _ = score_week(f[f.source == "baseline"], f[f.source == "ours"], act, platform="baseline")
    weekly.append({**row, "season": season, "week": int(w)})
wk = season_record(pd.DataFrame(weekly))
L = [f"# Pipeline dry run: {season} (SQLite, baseline as platform)", "",
     "| week | n | MAE ours | MAE baseline | winner | record |", "|---|---|---|---|---|---|"]
L += [f"| {r.week} | {r.n_scored} | {r.mae_ours:.2f} | {r.mae_platform:.2f} | {r.winner} | {r.record} |" for r in wk.itertuples()]
frozen_n = c.execute("SELECT COUNT(*) FROM frozen_projections").fetchone()[0]
L += ["", f"Frozen rows: {frozen_n}. Final record: **{wk.record.iloc[-1]}**."]
(PROJECT_ROOT / "reports" / f"dryrun_pipeline_{season}.md").write_text("\n".join(L) + "\n")
print("\n".join(L))
