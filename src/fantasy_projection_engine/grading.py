"""Live grading: who was inactive at kickoff, when a week is ready to score, and actual points.

Rules pre-registered in DECISIONS.md (2026-11-05, "Live grading"):
  1. a stat line or any offensive snap → active (overrides everything);
  2. otherwise roster status ACT → active, scores 0;
  3. otherwise inactive (INA / RES / DEV / cut / no roster row) → removed from every source's pool and logged.
"""

import pandas as pd

PROVISIONAL_DAYS = 10   # results are re-scored for stat corrections until this many days after the week's last game


def evidence_of_play(stats: pd.DataFrame, snaps: pd.DataFrame, players: pd.DataFrame, season: int, week: int) -> set:
    """player_ids (gsis) with a stat line or at least one offensive snap in that week."""
    s = stats[(stats["season"] == season) & (stats["week"] == week)]
    ids = set(s["player_id"])
    sn = snaps[(snaps["season"] == season) & (snaps["week"] == week) & (snaps["offense_snaps"] > 0)]
    xwalk = players[["gsis_id", "pfr_id"]].dropna().drop_duplicates("pfr_id")
    ids |= set(sn.merge(xwalk, left_on="pfr_player_id", right_on="pfr_id")["gsis_id"])
    return ids


def inactive_players(player_ids, played: set, roster_week: pd.DataFrame, out_ids=()) -> pd.DataFrame:
    """Which of `player_ids` were inactive at kickoff. roster_week: that week's roster rows (gsis_id, status).
    Returns player_id, reason ('designated_out' if Out on the final injury report, else 'inactive_at_kickoff')."""
    status = roster_week.drop_duplicates("gsis_id").set_index("gsis_id")["status"]
    out_ids = set(out_ids)
    rows = [(p, "designated_out" if p in out_ids else "inactive_at_kickoff") for p in dict.fromkeys(player_ids)
            if p not in played and status.get(p) != "ACT"]
    return pd.DataFrame(rows, columns=["player_id", "reason"])


def week_ready(schedules: pd.DataFrame, stats: pd.DataFrame, rosters_weekly: pd.DataFrame, season: int, week: int) -> tuple[bool, str]:
    """Can week W be scored yet? All games final, stat lines present, and a week-W roster for every team that played."""
    g = schedules[(schedules["season"] == season) & (schedules["week"] == week) & (schedules["game_type"] == "REG")]
    if g.empty:
        return False, f"no regular-season games in week {week}"
    if g["home_score"].isna().any():
        return False, f"{int(g['home_score'].isna().sum())} game(s) not final yet"
    if not ((stats["season"] == season) & (stats["week"] == week)).any():
        return False, "nflverse has no stat lines for this week yet"
    teams = set(g["home_team"]) | set(g["away_team"])
    r = rosters_weekly[(rosters_weekly["season"] == season) & (rosters_weekly["week"] == week)]
    missing = teams - set(r["team"])
    if missing:
        return False, f"week-{week} rosters missing for {len(missing)} team(s)"
    return True, "ready"


def is_final(schedules: pd.DataFrame, season: int, week: int, now: str) -> bool:
    """True once PROVISIONAL_DAYS have passed since the week's last game day (no more re-scoring)."""
    g = schedules[(schedules["season"] == season) & (schedules["week"] == week) & (schedules["game_type"] == "REG")]
    last = pd.Timestamp(g["gameday"].max(), tz="UTC") + pd.Timedelta(days=1)   # end of the last game day
    return pd.Timestamp(now) >= last + pd.Timedelta(days=PROVISIONAL_DAYS)


def actual_points(stats: pd.DataFrame, frozen: pd.DataFrame, season: int, week: int) -> pd.DataFrame:
    """Actual PPR points for every frozen player who has a stat line (absent = no stat line, scored 0 if active)."""
    s = stats[(stats["season"] == season) & (stats["week"] == week)][["player_id", "fantasy_points_ppr"]]
    keys = frozen[["player_id", "game_id"]].drop_duplicates()
    a = keys.merge(s, on="player_id", how="inner").rename(columns={"fantasy_points_ppr": "points_ppr"})
    return a.assign(season=season, week=week).dropna(subset=["points_ppr"])
