"""Betting-market inputs: closing spread and over/under → each team's implied points and margin.

nflverse schedules give, per game:
  spread_line  closing spread; POSITIVE = home team favoured by that many points
  total_line   closing over/under (expected combined points)

For each team in each game:
  implied points  = (total + own margin) / 2
  expected margin = +spread for the home team, −spread for the away team

Example: BUF @ BAL, total 39, spread 7.5 → BAL 23.25 (margin +7.5), BUF 15.75 (margin −7.5).

These are CLOSING lines (final number at kickoff). Our projections are frozen at kickoff,
so using them is not look-ahead. Live use needs a pre-kickoff odds source (see DECISIONS.md).
"""

import numpy as np
import pandas as pd

from .opp_eff import decayed_prior_sum

TEAM_ALIASES = {"OAK": "LV"}


def build_team_lines(schedules: pd.DataFrame) -> pd.DataFrame:
    s = schedules[schedules["game_type"] == "REG"]
    sides = []
    for side, sign in [("home", 1), ("away", -1)]:
        t = s[["game_id", "season", "week"]].copy()
        t["team"] = s[f"{side}_team"].replace(TEAM_ALIASES)
        t["margin"] = sign * s["spread_line"]
        t["implied"] = (s["total_line"] + sign * s["spread_line"]) / 2
        sides.append(t)
    return pd.concat(sides, ignore_index=True)


def add_lines(player_games: pd.DataFrame, team_lines: pd.DataFrame) -> pd.DataFrame:
    out = player_games.merge(team_lines[["team", "game_id", "implied", "margin"]], on=["team", "game_id"], how="left")
    missing = out["implied"].isna().sum()
    if missing:
        raise ValueError(f"{missing} player-games have no betting line (team/game_id mismatch)")
    return out


def predict_team_volume(tg: pd.DataFrame, col: str, hl: float, use_lines: bool = True) -> np.ndarray:
    """Expected team volume per team-game from history + betting lines, walk-forward by season.

    tg: one row per team-game with columns team, season, week, `col`, implied, margin.
    Model (OLS):  col = b0 + b1 · hist + b2 · implied + b3 · margin
      hist = team's decayed average of `col` over its EARLIER games (half-life hl)
    Coefficients used for season s are fitted only on team-games from seasons < s.
    The first season has no earlier data, so it falls back to `hist`.
    use_lines=False drops implied/margin (control model: col = b0 + b1 · hist), which isolates
    the team-level regression-to-the-mean from the betting-market information.
    Returns predictions aligned with tg's row order.
    """
    order = np.lexsort((tg["week"].to_numpy(), tg["season"].to_numpy(), tg["team"].to_numpy()))
    t = tg.iloc[order].reset_index(drop=True)
    teams = t["team"].to_numpy()
    w = decayed_prior_sum(np.ones(len(t)), teams, hl)
    hist = np.where(w > 0, decayed_prior_sum(t[col].to_numpy(float), teams, hl) / np.where(w > 0, w, 1), np.nan)
    cols = [np.ones(len(t)), hist] + ([t["implied"].to_numpy(), t["margin"].to_numpy()] if use_lines else [])
    X = np.column_stack(cols)
    y = t[col].to_numpy(float)
    seasons = t["season"].to_numpy()
    pred = hist.copy()
    for s in np.unique(seasons):
        train = (seasons < s) & ~np.isnan(hist)
        if train.sum() < 50:
            continue
        b = np.linalg.lstsq(X[train], y[train], rcond=None)[0]
        here = seasons == s
        pred[here] = X[here] @ b
    out = np.empty(len(t))
    out[order] = pred
    return out
