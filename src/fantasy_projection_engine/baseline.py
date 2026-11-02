"""Naive baseline: trailing (weighted) average of a player's previous PPR games.

This is the bar every later model must beat (CLAUDE.md model step 1).

No look-ahead: for each player we sort games in time order and SHIFT by one
before averaging, so the projection for game g only sees games before g.
History carries across seasons (a Week 1 projection uses last year's games).
"""

import pandas as pd

from . import SKILL_POSITIONS
from .metrics import mae, rmse

# Top-N per position, mirroring the Big 60 (10 QB, 20 RB, 20 WR, 10 TE)
BIG60_SLOTS = {"QB": 10, "RB": 20, "WR": 20, "TE": 10}


def prepare_games(player_games: pd.DataFrame, include_snap_zeros: bool = True) -> pd.DataFrame:
    """One row per player-game in time order (input: player_games.build_player_games).

    include_snap_zeros=False reproduces the Phase 1 behaviour for comparison: the
    zero-point snap-only games are still in the table (so they get scored), but
    their points are hidden from the history (`hist`), so averages skip them.
    """
    g = player_games.rename(columns={"fantasy_points_ppr": "actual"}).copy()
    g["hist"] = g["actual"]
    if not include_snap_zeros:
        g.loc[g["source"] == "snaps_only", "hist"] = float("nan")
    return g.sort_values(["player_id", "season", "week"]).reset_index(drop=True)


# Each method maps a player's PAST points (already shifted) to a projection.
METHODS = {
    "last_game": lambda past: past,
    "last3_mean": lambda past: past.rolling(3, min_periods=1).mean(),
    "last8_mean": lambda past: past.rolling(8, min_periods=1).mean(),
    "career_mean": lambda past: past.expanding().mean(),
    **{f"ewma_hl{h}": (lambda past, h=h: past.ewm(halflife=h, ignore_na=True).mean()) for h in (2, 4, 8, 16)},
}


def add_projection(games: pd.DataFrame, method: str, col: str = "proj") -> pd.DataFrame:
    """Add a column of walk-forward projections. Players' first-ever game gets NaN."""
    fn = METHODS[method]
    out = games.copy()
    hist = out["hist"] if "hist" in out else out["actual"]
    past = hist.groupby(out["player_id"]).shift(1)  # <- the leakage guard
    out[col] = past.groupby(out["player_id"]).transform(fn)
    return out


# Wider "fantasy-relevant" pool used as the tuning population (option A, DECISIONS.md)
RELEVANT_SLOTS = {"QB": 15, "RB": 30, "WR": 30, "TE": 15}


def big60_pool(df: pd.DataFrame, proj_col: str = "proj", slots: dict = BIG60_SLOTS) -> pd.DataFrame:
    """Each week's top-N per position BY PROJECTION (pre-game info only)."""
    d = df.dropna(subset=[proj_col])
    d = d.assign(_rank=d.groupby(["season", "week", "position"])[proj_col].rank(ascending=False, method="first"))
    keep = d["_rank"] <= d["position"].map(slots)
    return d[keep].drop(columns="_rank")


def score(df: pd.DataFrame, proj_col: str = "proj") -> dict:
    d = df.dropna(subset=[proj_col])
    return {
        "n": len(d),
        "mae": mae(d["actual"], d[proj_col]),
        "rmse": rmse(d["actual"], d[proj_col]),
        # Spearman = Pearson correlation of the ranks (no scipy needed)
        "spearman": float(d["actual"].rank().corr(d[proj_col].rank())),
    }
