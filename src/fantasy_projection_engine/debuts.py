"""Projections for starting QBs with no NFL starts yet (DECISIONS.md 2026-11-12, "First-start QBs").

Our model builds every projection from a player's own past games, so a QB about to make his first career start
(Kyle McCord and Carson Beck, week 10 of 2026) had no projection at all. For them we use what QBs in exactly that
situation have scored: every first career start by a QB who entered the league in 2018 or later, 2018–2023
(development seasons only). The median is our projection; the 10th / 90th percentiles are the floor / ceiling.
No player-specific adjustment: with no NFL games there is nothing to shrink toward the position average, so the
projection IS the position average for the situation (the fully-pooled end of empirical Bayes).

Who gets one (live): listed QB1 on his team's latest depth chart, active on the pre-game roster, not already
projected by the model, and no career start in our data (2018 onward).
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

FILE = Path(__file__).resolve().parents[2] / "reports" / "debuts.json"
EXPLANATION = "first career start: typical first start by a QB, 2018–2023 (no NFL games of his own yet)"


def starting_qbs(schedules: pd.DataFrame) -> pd.DataFrame:
    """game_id, season, week, team, player_id for each listed starting QB (a pre-game fact in nflverse schedules)."""
    s = schedules[schedules["game_type"] == "REG"]
    return pd.concat([s[["game_id", "season", "week", "home_team", "home_qb_id"]].set_axis(["game_id", "season", "week", "team", "player_id"], axis=1),
                      s[["game_id", "season", "week", "away_team", "away_qb_id"]].set_axis(["game_id", "season", "week", "team", "player_id"], axis=1)],
                     ignore_index=True).dropna(subset=["player_id"])


def first_starts(schedules: pd.DataFrame, pg: pd.DataFrame, players: pd.DataFrame) -> pd.DataFrame:
    """Each QB's first career start, for QBs whose rookie season is 2018+ (so the start really is his first in our
    data), with his PPR points that game. A starter with no stat line scored 0."""
    rookie = players.drop_duplicates("gsis_id").set_index("gsis_id")["rookie_season"]
    st = starting_qbs(schedules).sort_values(["season", "week"])
    st = st[st["player_id"].map(rookie).ge(2018)].groupby("player_id").head(1)
    pts = pg[["game_id", "player_id", "fantasy_points_ppr"]]
    return st.merge(pts, on=["game_id", "player_id"], how="left").fillna({"fantasy_points_ppr": 0.0})


def estimate(first: pd.DataFrame, seasons) -> dict:
    x = first.loc[first["season"].isin(list(seasons)), "fantasy_points_ppr"]
    return {"n": int(len(x)), "floor": float(x.quantile(0.1)), "median": float(x.median()),
            "ceiling": float(x.quantile(0.9)), "mean": float(x.mean())}


def validate(first: pd.DataFrame, est: dict, season: int) -> dict:
    """Out-of-sample check on one held-out season: MAE of the median, and floor–ceiling coverage (target ~80%)."""
    x = first.loc[first["season"] == season, "fantasy_points_ppr"].to_numpy(float)
    return {"season": season, "n": int(len(x)), "mae": float(np.abs(x - est["median"]).mean()),
            "coverage": float(((x >= est["floor"]) & (x <= est["ceiling"])).mean())}


def load() -> dict:
    return json.loads(FILE.read_text())["estimate"]


def qb1_from_depth(depth: pd.DataFrame, at: str | None = None) -> pd.DataFrame:
    """team, player_id of each team's QB1 on the latest depth-chart snapshot taken at or before `at` (UTC ISO)."""
    d = depth if at is None else depth[depth["dt"] <= at]
    d = d[d["dt"] == d["dt"].max()]
    q = d[(d["pos_abb"] == "QB") & (d["pos_rank"] == 1)]
    return q[["team", "gsis_id"]].rename(columns={"gsis_id": "player_id"}).dropna().drop_duplicates("team")


def debut_rows(qb1: pd.DataFrame, roster: pd.DataFrame, projected_ids, schedules: pd.DataFrame, players: pd.DataFrame,
               season: int, week: int, est: dict) -> pd.DataFrame:
    """Projection rows (same columns predict() publishes) for QB1s with no career start who aren't projected yet."""
    s = schedules[(schedules["game_type"] == "REG") & (schedules["season"] == season) & (schedules["week"] == week)]
    team_game = {**dict(zip(s["home_team"], s["game_id"])), **dict(zip(s["away_team"], s["game_id"]))}
    started = set(starting_qbs(schedules[schedules["home_score"].notna()])["player_id"])
    active = roster.loc[roster["status"] == "ACT", ["player_id", "team"]]
    q = qb1.merge(active, on=["player_id", "team"])
    pl = players.drop_duplicates("gsis_id").set_index("gsis_id")
    veteran = q["player_id"].map(pl["rookie_season"]).lt(2018)        # pre-2018 careers aren't in our data: skip
    q = q[~q["player_id"].isin(set(projected_ids)) & ~q["player_id"].isin(started) & q["team"].isin(team_game) & ~veteran]
    names = pl["display_name"]
    return pd.DataFrame({"player_id": q["player_id"].to_numpy(), "player_display_name": q["player_id"].map(names).to_numpy(),
                         "position": "QB", "team": q["team"].to_numpy(), "game_id": q["team"].map(team_game).to_numpy(),
                         "season": season, "week": week, "median": est["median"], "floor": est["floor"],
                         "ceiling": est["ceiling"], "step_baseline": np.nan, "explanation": EXPLANATION})
