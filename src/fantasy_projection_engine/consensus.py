"""Platform projections for the Big 60: Sleeper (projections supplied by RotoWire).

Rules pre-registered in DECISIONS.md (2026-11-05, "Sleeper joins the Big 60"):
- one API call per refresh; every snapshot kept (not public);
- Sleeper's projected STAT LINES are rescored under the nflverse PPR rule, so every source is graded on the same scoring;
- matched to nflverse ids via rosters' sleeper_id; teams map directly except LAR → LA.
"""

import json
import urllib.request
from pathlib import Path

import pandas as pd

SOURCE = "sleeper"
LABEL = "Sleeper (projections by RotoWire)"
POSITIONS = ("QB", "RB", "WR", "TE")
TEAM_MAP = {"LAR": "LA"}
URL = "https://api.sleeper.com/projections/nfl/{season}/{week}?season_type=regular" + "".join(
    f"&position%5B%5D={p}" for p in POSITIONS)

# nflverse full-PPR rule (reproduces every 2025 fantasy_points_ppr exactly), in Sleeper's stat names.
NFLVERSE_PPR = {"pass_yd": 0.04, "pass_td": 4, "pass_int": -2, "pass_2pt": 2, "rush_yd": 0.1, "rush_td": 6, "rush_2pt": 2,
                "rec": 1, "rec_yd": 0.1, "rec_td": 6, "rec_2pt": 2, "fum_lost": -2}


def fetch_sleeper(season: int, week: int, timeout: int = 30) -> list[dict]:
    req = urllib.request.Request(URL.format(season=season, week=week),
                                 headers={"User-Agent": "fantasy-projection-engine (non-commercial research)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


CACHE = "sleeper_projections.json"   # saved in the refresh's download folder so the snapshot step reuses the same call


def fetch_sleeper_cached(folder, season: int, week: int, now: str, max_age_min: int = 45) -> tuple[list[dict], str]:
    """(raw, fetched_at). Reuses folder/CACHE if it is for this season/week and under max_age_min old; else fetches and
    saves it. Keeps the pre-registered "one API call per refresh" even though two steps read Sleeper."""
    from datetime import datetime
    f = Path(folder) / CACHE
    if f.exists():
        c = json.loads(f.read_text())
        age = (datetime.fromisoformat(now.replace("Z", "+00:00")) -
               datetime.fromisoformat(c["fetched_at"].replace("Z", "+00:00"))).total_seconds() / 60
        if c["season"] == season and c["week"] == week and 0 <= age <= max_age_min:
            return c["data"], c["fetched_at"]
    raw = fetch_sleeper(season, week)
    f.write_text(json.dumps({"season": season, "week": week, "fetched_at": now, "data": raw}))
    return raw, now


def rescore(stats: dict, rule: dict = NFLVERSE_PPR) -> float:
    """Projected points from a projected stat line under `rule` (missing stats count as 0)."""
    return float(sum(w * float(stats.get(k) or 0) for k, w in rule.items()))


def parse_sleeper(raw: list[dict], sleeper_to_gsis: pd.DataFrame, schedules: pd.DataFrame, season: int, week: int,
                  captured_at: str) -> tuple[pd.DataFrame, dict]:
    """Rows for consensus_snapshots. sleeper_to_gsis: columns sleeper_id, gsis_id. Returns (rows, counts)."""
    g = schedules[(schedules["season"] == season) & (schedules["week"] == week) & (schedules["game_type"] == "REG")]
    team_game = {**dict(zip(g["home_team"], g["game_id"])), **dict(zip(g["away_team"], g["game_id"]))}
    xw = sleeper_to_gsis.dropna().astype({"sleeper_id": str}).drop_duplicates("sleeper_id").set_index("sleeper_id")["gsis_id"]
    rows = []
    for x in raw:
        st, pl = x.get("stats") or {}, x.get("player") or {}
        pos = pl.get("position")
        if pos not in POSITIONS or st.get("pts_ppr") is None or int(x.get("week") or week) != week:
            continue
        team = TEAM_MAP.get(x.get("team"), x.get("team"))
        rows.append({"source": SOURCE, "source_player_id": str(x["player_id"]), "player_id": xw.get(str(x["player_id"])),
                     "season": season, "week": week, "position": pos, "team": team, "game_id": team_game.get(team),
                     "projected": rescore(st), "projected_platform": float(st["pts_ppr"]), "captured_at": captured_at})
    df = pd.DataFrame(rows)
    counts = {"rows": len(df), "unmatched_player": int(df["player_id"].isna().sum()) if len(df) else 0,
              "no_game": int(df["game_id"].isna().sum()) if len(df) else 0}
    return df, counts
