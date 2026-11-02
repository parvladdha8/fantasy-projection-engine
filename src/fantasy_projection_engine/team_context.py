"""Team-level volume: how many targets, carries and pass attempts each team had per game.

Used by the team-context model (opp_eff with CompParams.team=True):

    player volume = player's SHARE of team volume × team's EXPECTED volume

Team totals include every player on the team (all positions), so shares are true shares.
"""

import pandas as pd

TEAM_COLS = {"targets": "team_targets", "carries": "team_carries", "attempts": "team_attempts"}


def build_team_games(ps: pd.DataFrame) -> pd.DataFrame:
    """One row per team per regular-season game with total targets / carries / attempts."""
    reg = ps[ps["season_type"] == "REG"]
    t = reg.groupby(["team", "season", "week", "game_id"], as_index=False)[list(TEAM_COLS)].sum()
    return t.rename(columns=TEAM_COLS)


def add_team_totals(player_games: pd.DataFrame, team_games: pd.DataFrame) -> pd.DataFrame:
    """Attach the team's totals for that game to each player-game (by team + game)."""
    out = player_games.merge(team_games[["team", "game_id", *TEAM_COLS.values()]], on=["team", "game_id"], how="left")
    missing = out["team_targets"].isna().sum()
    if missing:
        raise ValueError(f"{missing} player-games have no matching team totals (team/game_id mismatch)")
    return out
