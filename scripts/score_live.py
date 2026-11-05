"""Live grading: score every week that has frozen projections, is ready, and is not yet final.

Steps per week (rules: DECISIONS.md 2026-11-05, "Live grading"):
  inactive at kickoff (stat line / snaps / roster status) → actual PPR points → Big 60 for each platform vs ours →
  replace that week's provisional rows. Weeks become final 10 days after their last game and are never recomputed.

Usage:
  uv run python scripts/score_live.py                    # Supabase, fresh download
  uv run python scripts/score_live.py --no-pull          # reuse the latest download
  uv run python scripts/score_live.py --sqlite PATH      # a local SQLite file (rehearsals)
"""

import sys

import pandas as pd

from fantasy_projection_engine import LIVE_SEASON
from fantasy_projection_engine.alerts import write_failure
from fantasy_projection_engine.data import latest_live, load_live, pull_live
from fantasy_projection_engine.grading import actual_points, evidence_of_play, inactive_players, is_final, week_ready
from fantasy_projection_engine.leaderboard import score_week, season_record
from fantasy_projection_engine.live import out_designations
from fantasy_projection_engine.storage import _sql, connect_postgres, connect_sqlite, save_grading, utc_now


def read(conn, q, params=()):
    cur = conn.cursor()
    cur.execute(_sql(conn, q), params)
    cols = [d[0] for d in cur.description]
    return pd.DataFrame(cur.fetchall(), columns=cols)


def grade(conn, season: int, pull, now: str | None = None) -> list[str]:
    """Grade all eligible weeks of `season` using the live download `pull`. Returns printable lines."""
    now = now or utc_now()
    tab = {t: load_live(season, t, pull) for t in ("schedules", "player_stats_week", "snap_counts", "players", "rosters_weekly", "injuries")}
    stats = tab["player_stats_week"]
    stats = stats[stats["season_type"] == "REG"]
    out = []
    weeks = read(conn, "SELECT DISTINCT week FROM frozen_projections WHERE season = ? ORDER BY week", (season,))["week"].tolist()
    scored = set(read(conn, "SELECT DISTINCT week FROM leaderboard_weekly WHERE season = ?", (season,))["week"].tolist())
    for w in weeks:
        w = int(w)
        if w in scored and is_final(tab["schedules"], season, w, now):
            out.append(f"week {w}: final (not recomputed)")
            continue
        ok, why = week_ready(tab["schedules"], stats, tab["rosters_weekly"], season, w)
        if not ok:
            out.append(f"week {w}: not ready ({why}); will try again next run")
            continue
        f = read(conn, "SELECT * FROM frozen_projections WHERE season = ? AND week = ?", (season, w))
        played = evidence_of_play(stats, tab["snap_counts"], tab["players"], season, w)
        roster_w = tab["rosters_weekly"][(tab["rosters_weekly"]["season"] == season) & (tab["rosters_weekly"]["week"] == w)]
        outs = set(out_designations(tab["injuries"], season, w)["player_id"])
        inact = inactive_players(f["player_id"], played, roster_w, outs)
        inact = inact.merge(f[["player_id", "game_id"]].drop_duplicates("player_id"), on="player_id")
        act = actual_points(stats, f, season, w)
        ours = f[f["source"] == "ours"]
        weekly, positions = [], []
        week_games = set(tab["schedules"].loc[(tab["schedules"]["season"] == season) & (tab["schedules"]["week"] == w) &
                                              (tab["schedules"]["game_type"] == "REG"), "game_id"])
        for src in sorted(set(f["source"]) - {"ours"}):
            missing = week_games - set(f.loc[f["source"] == src, "game_id"])
            if missing:   # partial week: the platform's pool would be biased, so it is not graded (pre-registered)
                out.append(f"week {w} vs {src}: NOT graded, {len(missing)} of {len(week_games)} games have no frozen {src} snapshot")
                continue
            row, pos, _ = score_week(f[f["source"] == src], ours, act, inact["player_id"], platform=src)
            weekly.append(row)
            positions.append(pos)
        if not weekly:
            out.append(f"week {w}: no platform frozen yet; nothing to score")
            continue
        save_grading(conn, season, w, act, inact, weekly, pd.concat(positions, ignore_index=True), now=now)
        status = "final" if is_final(tab["schedules"], season, w, now) else "provisional (re-scored daily for stat corrections)"
        for r in weekly:
            out.append(f"week {w} vs {r['platform']}: MAE ours {r['mae_ours']:.3f} vs {r['mae_platform']:.3f} → {r['winner']}; "
                       f"pool {r['n_pool']}, scored {r['n_scored']}, inactive removed {r['n_inactive']}, "
                       f"dropped (no projection of ours) {r['n_dropped_no_ours']}; {status}")
    lb = read(conn, "SELECT platform, season, week, winner FROM leaderboard_weekly WHERE season = ?", (season,))
    if len(lb):
        rec = season_record(lb).groupby("platform").tail(1)
        out += [f"season record vs {r.platform}: {r.record}" for r in rec.itertuples()]
    return out


def main(argv):
    season = LIVE_SEASON
    pull = latest_live(season) if "--no-pull" in argv else pull_live(season)
    conn = connect_sqlite(argv[argv.index("--sqlite") + 1]) if "--sqlite" in argv else connect_postgres()
    print(f"grading {season} with data pull {pull.name}")
    print("\n".join(grade(conn, season, pull)))
    conn.close()


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except Exception as e:
        print(write_failure("weekly grading (actual points → Big 60)", e))
        raise SystemExit(1)
