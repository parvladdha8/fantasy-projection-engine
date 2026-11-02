"""Opportunity × Efficiency model (CLAUDE.md model step 2).

Projected points = Σ over components [ expected volume × expected points-per-opportunity ] + other

  component  volume ("opportunity")   efficiency
  ---------  ----------------------   -------------------------------------------
  rec        targets                  (receptions + 0.1·yds + 6·TD + 2·2pt) / target
  rush       carries                  (0.1·yds + 6·TD + 2·2pt) / carry
  pass       pass attempts            (yds/25 + 4·TD − 2·INT + 2·2pt) / attempt
  other      —                        fumbles lost (−2), return TDs (+6): plain EWMA

Volume: exponentially weighted average of past games (half-life `hl_vol` games).

Efficiency: empirical-Bayes shrinkage toward the position's league-wide rate:

    eff = (S_pts + k · μ_pos) / (S_opp + k)

  S_pts, S_opp = player's decayed sums of points and opportunities (half-life `hl_eff`)
  μ_pos        = position league rate using ONLY games from earlier weeks
  k            = prior strength, in "pseudo-opportunities" of league-average play

  Shrinkage share = k / (S_opp + k): 1 = fully league average, 0 = fully the player's own.

No look-ahead: every sum covers games strictly before the one being projected.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

COMPONENTS = {
    "rec": "targets",
    "rush": "carries",
    "pass": "attempts",
}


@dataclass(frozen=True)
class CompParams:
    hl_vol: float  # half-life (games) for volume
    hl_eff: float  # half-life (games) for efficiency sums
    k: float       # shrinkage prior strength (pseudo-opportunities)


DEFAULT_PARAMS = {
    "rec": CompParams(hl_vol=4, hl_eff=16, k=50),
    "rush": CompParams(hl_vol=4, hl_eff=16, k=50),
    "pass": CompParams(hl_vol=4, hl_eff=16, k=100),
    "other_hl": 16,
}


def add_components(df: pd.DataFrame) -> pd.DataFrame:
    """Split each game's PPR points into rec / rush / pass / other (they sum to the total)."""
    d = df.copy()
    d["pts_rec"] = d["receptions"] + 0.1 * d["receiving_yards"] + 6 * d["receiving_tds"] + 2 * d["receiving_2pt_conversions"]
    d["pts_rush"] = 0.1 * d["rushing_yards"] + 6 * d["rushing_tds"] + 2 * d["rushing_2pt_conversions"]
    d["pts_pass"] = (
        d["passing_yards"] / 25 + 4 * d["passing_tds"] - 2 * d["passing_interceptions"] + 2 * d["passing_2pt_conversions"]
    )
    d["pts_other"] = -2 * (d["rushing_fumbles_lost"] + d["receiving_fumbles_lost"] + d["sack_fumbles_lost"]) + 6 * d["special_teams_tds"]
    return d


def decayed_prior_sum(x: np.ndarray, groups: np.ndarray, halflife: float) -> np.ndarray:
    """For each row t: Σ_{j<t, same group} d^(t−1−j) · x_j, with d = 0.5^(1/halflife).

    Rows must be sorted by group then time. Excludes the current row (no look-ahead).
    """
    d = 0.5 ** (1.0 / halflife)
    out = np.empty(len(x))
    s = 0.0
    prev = None
    for i in range(len(x)):
        if groups[i] != prev:
            s, prev = 0.0, groups[i]
        out[i] = s
        s = d * s + x[i]
    return out


def league_rate(df: pd.DataFrame, pts_col: str, opp_col: str) -> pd.Series:
    """Position-level points per opportunity using only weeks BEFORE each row's week."""
    wk = df["season"] * 100 + df["week"]
    tot = df.assign(_wk=wk).groupby(["position", "_wk"])[[pts_col, opp_col]].sum().sort_index()
    cum = tot.groupby(level="position").cumsum().groupby(level="position").shift(1)  # strictly earlier weeks
    rate = (cum[pts_col] / cum[opp_col]).rename("mu")
    keys = pd.MultiIndex.from_arrays([df["position"], wk])
    return pd.Series(rate.reindex(keys).to_numpy(), index=df.index)


def project(games: pd.DataFrame, params: dict = DEFAULT_PARAMS, sums_cache: dict | None = None) -> pd.DataFrame:
    """Add projection columns. `games` must be sorted by player_id, season, week.

    Adds per component c: vol_c, eff_c, shrink_c, proj_c; plus proj_other and proj (total).
    sums_cache lets a parameter search reuse decayed sums for the same half-life.
    """
    d = add_components(games) if "pts_rec" not in games else games.copy()
    g = d["player_id"].to_numpy()
    cache = {} if sums_cache is None else sums_cache

    def dsum(col, hl):
        key = (col, hl)
        if key not in cache:
            cache[key] = decayed_prior_sum(d[col].to_numpy(float), g, hl)
        return cache[key]

    ones = "_one"
    d[ones] = 1.0
    total = np.zeros(len(d))
    for c, opp in COMPONENTS.items():
        p = params[c]
        w = dsum(ones, p.hl_vol)
        vol = np.where(w > 0, dsum(opp, p.hl_vol) / np.where(w > 0, w, 1), np.nan)
        s_opp, s_pts = dsum(opp, p.hl_eff), dsum(f"pts_{c}", p.hl_eff)
        if ("mu", c) not in cache:
            cache[("mu", c)] = league_rate(d, f"pts_{c}", opp).to_numpy()
        mu = cache[("mu", c)]
        eff = (s_pts + p.k * mu) / (s_opp + p.k) if p.k > 0 else np.where(s_opp > 0, s_pts / np.where(s_opp > 0, s_opp, 1), mu)
        d[f"vol_{c}"], d[f"eff_{c}"] = vol, eff
        d[f"shrink_{c}"] = p.k / (s_opp + p.k) if p.k > 0 else 0.0
        d[f"proj_{c}"] = vol * eff
        total = total + d[f"proj_{c}"].to_numpy()
    w = dsum(ones, params["other_hl"])
    d["proj_other"] = np.where(w > 0, dsum("pts_other", params["other_hl"]) / np.where(w > 0, w, 1), np.nan)
    d["proj"] = total + d["proj_other"].to_numpy()
    return d.drop(columns=ones)
