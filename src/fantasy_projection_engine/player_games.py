"""Build the complete player-game table: one row per skill player per game he played.

Problem: nflverse weekly stats only contain a player-game if the player recorded a
stat. An active WR with 0 targets is simply missing, so a trailing average skips
his true zeros (biased upward) and our evaluation never scores those games.

Fix: snap counts (from Pro Football Reference) list everyone who took a snap.
Any skill player with >= 1 offensive snap but no stats row gets a row with
0 fantasy points. Snap data uses PFR IDs, so we map them to nflverse (gsis) IDs
via the players table.

Matching rules (see DECISIONS.md):
  * Match on (player ID, game) only. PFR position labels differ (FB, HB, two-way),
    so position always comes from nflverse.
  * Stats rows are never dropped: a stat proves the player played.
"""

import pandas as pd

from . import SKILL_POSITIONS

# Box-score columns carried through (0 for snap-only games)
STAT_COLS = [
    "attempts", "passing_yards", "passing_tds", "passing_interceptions", "passing_2pt_conversions",
    "carries", "rushing_yards", "rushing_tds", "rushing_2pt_conversions",
    "targets", "receptions", "receiving_yards", "receiving_tds", "receiving_2pt_conversions",
    "rushing_fumbles_lost", "receiving_fumbles_lost", "sack_fumbles_lost", "special_teams_tds",
]


def build_player_games(ps: pd.DataFrame, snaps: pd.DataFrame, players: pd.DataFrame) -> pd.DataFrame:
    stats = ps[(ps["season_type"] == "REG") & (ps["position"].isin(SKILL_POSITIONS))]
    stats = stats[["player_id", "player_display_name", "position", "team", "season", "week", "game_id", "fantasy_points_ppr", *STAT_COLS]]
    stats = stats.fillna({c: 0 for c in STAT_COLS})

    xwalk = players[["gsis_id", "pfr_id", "display_name", "position"]].dropna(subset=["gsis_id", "pfr_id"])
    sn = snaps[snaps["game_type"] == "REG"].merge(xwalk, left_on="pfr_player_id", right_on="pfr_id", how="inner")
    sn = sn.rename(columns={"gsis_id": "player_id", "position_y": "players_position"})
    sn = sn[["player_id", "game_id", "team", "season", "week", "display_name", "players_position", "offense_snaps", "offense_pct"]]
    sn = sn.drop_duplicates(["player_id", "game_id"])

    # 1) stats rows, with snaps attached where available
    out = stats.merge(sn[["player_id", "game_id", "offense_snaps", "offense_pct"]], on=["player_id", "game_id"], how="left")
    out["source"] = "stats"

    # 2) snap-only rows -> true zero-point games
    flagged = sn.merge(stats[["player_id", "game_id"]], on=["player_id", "game_id"], how="left", indicator=True)
    extra = flagged[(flagged["_merge"] == "left_only") & (flagged["offense_snaps"] > 0)].drop(columns="_merge").copy()
    # position: player's most common nflverse stats position; else players-table position
    stats_pos = stats.groupby("player_id")["position"].agg(lambda s: s.mode().iat[0])
    extra["position"] = extra["player_id"].map(stats_pos).fillna(extra["players_position"])
    extra = extra[extra["position"].isin(SKILL_POSITIONS)]
    extra = extra.rename(columns={"display_name": "player_display_name"}).assign(fantasy_points_ppr=0.0, source="snaps_only", **{c: 0.0 for c in STAT_COLS})
    # snap team labels can differ (e.g. OAK/LV); take team from the game for consistency
    extra["team"] = extra["team"].replace({"OAK": "LV"})

    cols = list(out.columns)
    out = pd.concat([out, extra[cols]], ignore_index=True)
    return out.sort_values(["player_id", "season", "week"]).reset_index(drop=True)
