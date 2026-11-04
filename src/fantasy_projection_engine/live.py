"""Live rows: build player rows for games that haven't been played yet, so predict() can project them.

Rule (DECISIONS.md, 2026-11-03): a player's team comes from the pre-game roster (trades/signings), falling back
to his last game's team; he must have played this season (Week 1: last season) and not be on a reserve list,
practice squad, cut or retired, or designated Out.
Upcoming rows carry the game's betting line; every outcome column (points, stats, snaps, team totals) is NaN.
Because every model piece only uses EARLIER rows, a NaN in the newest row never feeds anything else.
"""

import numpy as np
import pandas as pd

from .baseline import prepare_games
from .betting import add_lines, build_team_lines
from .data import load_live, load_player_stats, load_players, load_rosters_weekly, load_schedules, load_snap_counts
from .opp_eff import add_components
from .player_games import STAT_COLS, build_player_games
from .team_context import TEAM_COLS, add_team_totals, build_team_games

OUTCOME_COLS = ["fantasy_points_ppr", *STAT_COLS, "offense_snaps", "offense_pct", *TEAM_COLS.values()]


EXCLUDED_STATUS = ("RES", "DEV", "CUT", "RET")  # reserve/IR, practice squad, cut, retired (pre-game transactions)


def candidates(pg: pd.DataFrame, schedules: pd.DataFrame, season: int, week: int,
               roster: pd.DataFrame | None = None) -> pd.DataFrame:
    """Upcoming player rows for (season, week): the pre-game identity of each candidate, outcomes NaN.

    roster (optional): columns player_id, team, status, as known BEFORE the game. Its team overrides the
    last-game team (trades/signings); excluded statuses are dropped. Without it: the last-game rule
    (most recent team, and played for it this season)."""
    s = schedules[(schedules["game_type"] == "REG") & (schedules["season"] == season) & (schedules["week"] == week)]
    sides = pd.concat([s[["game_id", "home_team"]].rename(columns={"home_team": "team"}),
                       s[["game_id", "away_team"]].rename(columns={"away_team": "team"})], ignore_index=True)
    past = pg[(pg["season"] < season) | ((pg["season"] == season) & (pg["week"] < week))]
    last = past.sort_values(["season", "week"]).groupby("player_id").tail(1)
    week1 = week == 1 or not (past["season"] == season).any()
    if roster is None:
        if week1:
            last = last[last["season"] == season - 1]
        else:
            this = past[past["season"] == season][["player_id", "team"]].drop_duplicates()
            last = last.merge(this, on=["player_id", "team"])  # most recent team, AND played for it this season
    else:
        last = last[last["season"] == (season - 1 if week1 else season)]  # active recently (any team)
        r = roster.drop_duplicates("player_id")
        last = last.merge(r[["player_id", "team", "status"]].rename(columns={"team": "roster_team"}), on="player_id", how="left")
        last = last[~last["status"].isin(EXCLUDED_STATUS)]
        last["team"] = last["roster_team"].fillna(last["team"])
    rows = last[["player_id", "player_display_name", "position", "team"]].merge(sides, on="team")
    rows = rows.assign(season=season, week=week, source="upcoming", **{c: np.nan for c in OUTCOME_COLS})
    return rows


def assemble(pg_played: pd.DataFrame, upcoming: pd.DataFrame, schedules: pd.DataFrame) -> pd.DataFrame:
    """Played player-games (with team totals) + upcoming rows → the game table predict() expects."""
    lines = build_team_lines(schedules)
    up = add_lines(upcoming, lines)
    up = up[[c for c in pg_played.columns if c in up.columns]]
    games = pd.concat([pg_played, up], ignore_index=True)
    return add_components(prepare_games(games))


def played_table(ps: pd.DataFrame, snaps: pd.DataFrame, players: pd.DataFrame, schedules: pd.DataFrame) -> pd.DataFrame:
    pg = build_player_games(ps, snaps, players)
    return add_lines(add_team_totals(pg, build_team_games(ps)), build_team_lines(schedules))


def load_live_inputs(season: int, pull=None) -> dict:
    """Frozen 2018–25 tables + the live pull. Crosswalk: frozen players table, plus only NEW ids from the pull."""
    raw_players, live_players = load_players(), load_live(season, "players", pull)
    players = pd.concat([raw_players, live_players[~live_players["gsis_id"].isin(raw_players["gsis_id"])]], ignore_index=True)
    cat = lambda a, b: pd.concat([a, b[a.columns.intersection(b.columns)]], ignore_index=True)
    return {"ps": cat(load_player_stats(), load_live(season, "player_stats_week", pull)),
            "snaps": cat(load_snap_counts(), load_live(season, "snap_counts", pull)),
            "schedules": cat(load_schedules(), load_live(season, "schedules", pull)),
            "players": players,
            "injuries": load_live(season, "injuries", pull),
            "rosters_weekly": cat(load_rosters_weekly(), load_live(season, "rosters_weekly", pull)),
            "roster_now": load_live(season, "rosters", pull)}


def roster_for(inp: dict, season: int, week: int) -> tuple[pd.DataFrame, str]:
    """Pre-game roster for (season, week): the week-W weekly roster if published, else the current roster
    saved in our timestamped pull. Returns (player_id, team, status) and which source was used."""
    w = inp["rosters_weekly"]
    w = w[(w["season"] == season) & (w["week"] == week) & (w["game_type"] == "REG")]
    src, r = ("weekly roster", w) if len(w) else ("current roster (from this pull)", inp["roster_now"])
    return r[["gsis_id", "team", "status"]].rename(columns={"gsis_id": "player_id"}).dropna(subset=["player_id"]), src


def kickoffs(schedules: pd.DataFrame, season: int) -> pd.DataFrame:
    """game_id, week, kickoff (UTC ISO text) for a season's regular-season games. nflverse gives
    gameday + gametime in US Eastern time; the conversion handles daylight-saving changes."""
    s = schedules[(schedules["game_type"] == "REG") & (schedules["season"] == season)].dropna(subset=["gameday", "gametime"])
    ko = pd.to_datetime(s["gameday"] + " " + s["gametime"]).dt.tz_localize("America/New_York").dt.tz_convert("UTC")
    return pd.DataFrame({"game_id": s["game_id"].to_numpy(), "week": s["week"].to_numpy(),
                         "kickoff": ko.dt.strftime("%Y-%m-%dT%H:%M:%SZ").to_numpy()})


def next_week(schedules: pd.DataFrame, season: int) -> int:
    reg = schedules[(schedules["game_type"] == "REG") & (schedules["season"] == season)]
    up = reg[reg["home_score"].isna()]
    if up.empty:
        raise ValueError(f"no upcoming regular-season games in {season}")
    return int(up["week"].min())


def out_designations(injuries: pd.DataFrame, season: int, week: int) -> pd.DataFrame:
    """Players designated Out for that week (empty until the report is published)."""
    i = injuries[(injuries["season"] == season) & (injuries["week"] == week) & (injuries["game_type"] == "REG")]
    return i.loc[i["report_status"] == "Out", ["gsis_id", "report_status"]].rename(columns={"gsis_id": "player_id"})


def live_games(season: int, week: int | None = None, pull=None) -> tuple[pd.DataFrame, int, pd.DataFrame, str]:
    """Game table with history + upcoming rows for `week` (default: next unplayed week).
    Returns (games, week, excluded, roster source) — excluded = candidates removed because designated Out."""
    inp = load_live_inputs(season, pull)
    week = next_week(inp["schedules"], season) if week is None else week
    pg = played_table(inp["ps"], inp["snaps"], inp["players"], inp["schedules"])
    pg = pg[(pg["season"] < season) | ((pg["season"] == season) & (pg["week"] < week))]
    roster, src = roster_for(inp, season, week)
    up = candidates(pg, inp["schedules"], season, week, roster)
    out = out_designations(inp["injuries"], season, week)
    excluded = up[up["player_id"].isin(out["player_id"])][["player_id", "player_display_name", "position", "team"]]
    up = up[~up["player_id"].isin(out["player_id"])]
    return assemble(pg, up, inp["schedules"]), week, excluded, src
