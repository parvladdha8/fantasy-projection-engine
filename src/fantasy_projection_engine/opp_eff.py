"""Opportunity × Efficiency model (CLAUDE.md model step 2).

Projected points = Σ over components [ expected volume × expected points-per-opportunity ] + other

  component  volume ("opportunity")   efficiency
  ---------  ----------------------   -------------------------------------------
  rec        targets                  (receptions + 0.1·yds + 6·TD + 2·2pt) / target
  rush       carries                  (0.1·yds + 6·TD + 2·2pt) / carry
  pass       pass attempts            (yds/25 + 4·TD − 2·INT + 2·2pt) / attempt
  other      —                        fumbles lost (−2), return TDs (+6): plain EWMA

Volume: short-memory average of past games (half-life `hl_vol`), shrunk toward the
player's own long-run average (half-life `hl_long`) with prior strength `m` games:

    vol = (S_vol + m · long_run) / (W + m)

  S_vol, W = decayed sums of opportunities and of games (half-life hl_vol)
  m = 0 reproduces v1 (no volume shrinkage).

Team context (v3, CompParams.team=True): volume = share × expected team volume

  share      = (W · short_share + m · long_share) / (W + m)
               short/long_share = player's decayed opportunities ÷ his team's decayed
               totals IN THE SAME GAMES (half-lives hl_vol / hl_long). Same shrinkage
               structure as volume, applied to the role instead of the raw count.
  team_proj  = the team's decayed average total over its previous games (half-life hl_team).
               Uses the player's CURRENT team, so a traded player gets his new team's volume.

Betting lines (v4, CompParams.lines=True, requires team=True): team_proj comes from
  betting.predict_team_volume (history + implied points + spread, fitted on earlier seasons).

Efficiency: empirical-Bayes shrinkage toward the position's league-wide rate:

    eff = (S_pts + k · μ_pos) / (S_opp + k)

  S_pts, S_opp = player's decayed sums of points and opportunities (half-life `hl_eff`)
  μ_pos        = position league rate using ONLY games from earlier weeks
  k            = prior strength, in "pseudo-opportunities" of league-average play

  Shrinkage share = k / (S_opp + k): 1 = fully league average, 0 = fully the player's own.

No look-ahead: every sum covers games strictly before the one being projected.
"""

from dataclasses import dataclass

from .team_context import TEAM_COLS

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
    hl_long: float = 64  # half-life (games) of the long-run volume target
    m: float = 0         # volume shrinkage strength (pseudo-games); 0 = v1
    team: bool = False   # v3: volume = share × expected team volume
    hl_team: float = 8   # half-life (team games) for expected team volume
    lines: bool = False  # v4: team volume also uses betting lines (needs team=True)
    team_reg: bool = False  # v4-reg control: walk-forward regression on team history only (no lines)


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


def _dsum(d: pd.DataFrame, col: str, hl: float, cache: dict) -> np.ndarray:
    """Decayed prior sum of a column (or of 1s when col is None), memoised in `cache`."""
    key = (col, hl)
    if key not in cache:
        x = np.ones(len(d)) if col is None else d[col].to_numpy(float)
        cache[key] = decayed_prior_sum(x, d["player_id"].to_numpy(), hl)
    return cache[key]


def team_projection(d: pd.DataFrame, team_col: str, hl: float, cache: dict, lines: bool = False,
                    reg: bool = False) -> np.ndarray:
    """For each player-game: his team's expected `team_col`.

    default:   the team's decayed average over its earlier games.
    reg=True:  walk-forward regression on that history only (shrinks toward league average).
    lines=True: history + betting lines regression (betting.predict_team_volume).
    """
    key = ("team_proj", team_col, hl, lines, reg)
    if key not in cache:
        extra = ["implied", "margin"] if lines else []
        tg = d[["team", "season", "week", "game_id", team_col, *extra]].drop_duplicates(["team", "game_id"])
        tg = tg.sort_values(["team", "season", "week"]).reset_index(drop=True)
        if lines or reg:
            from .betting import predict_team_volume  # local import avoids a circular import
            tg["_proj"] = predict_team_volume(tg, team_col, hl, use_lines=lines)
        else:
            teams = tg["team"].to_numpy()
            s = decayed_prior_sum(tg[team_col].to_numpy(float), teams, hl)
            w = decayed_prior_sum(np.ones(len(tg)), teams, hl)
            tg["_proj"] = np.where(w > 0, s / np.where(w > 0, w, 1), np.nan)
        merged = d[["team", "game_id"]].merge(tg[["team", "game_id", "_proj"]], on=["team", "game_id"], how="left")
        cache[key] = merged["_proj"].to_numpy()
    return cache[key]


def _share(d: pd.DataFrame, opp: str, p: "CompParams", cache: dict) -> np.ndarray:
    """Player's shrunk share of team volume (see module docstring)."""
    tcol = TEAM_COLS[opp]
    w = _dsum(d, None, p.hl_vol, cache)
    short = _dsum(d, opp, p.hl_vol, cache) / np.where(w > 0, _dsum(d, tcol, p.hl_vol, cache), 1)
    if p.m > 0:
        w_long = _dsum(d, None, p.hl_long, cache)
        long = _dsum(d, opp, p.hl_long, cache) / np.where(w_long > 0, _dsum(d, tcol, p.hl_long, cache), 1)
        share = (w * short + p.m * long) / np.where(w + p.m > 0, w + p.m, 1)
    else:
        share = short
    return np.where(w > 0, share, np.nan)


def component_arrays(d: pd.DataFrame, c: str, p: CompParams, cache: dict) -> tuple[np.ndarray, ...]:
    """Volume, efficiency and shrinkage share for component c. `d` must already have components.

    `cache` must only ever be used with this same `d` (keys are column names).
    """
    opp = COMPONENTS[c]
    if p.team:
        vol = _share(d, opp, p, cache) * team_projection(d, TEAM_COLS[opp], p.hl_team, cache, p.lines, p.team_reg)
        return (vol, *_efficiency(d, c, p, cache))
    w = _dsum(d, None, p.hl_vol, cache)
    s_vol = _dsum(d, opp, p.hl_vol, cache)
    if p.m > 0:
        w_long = _dsum(d, None, p.hl_long, cache)
        long_run = _dsum(d, opp, p.hl_long, cache) / np.where(w_long > 0, w_long, 1)
        s_vol, w = s_vol + p.m * long_run, w + p.m * (w_long > 0)
    vol = np.where(w > 0, s_vol / np.where(w > 0, w, 1), np.nan)
    return (vol, *_efficiency(d, c, p, cache))


def _efficiency(d: pd.DataFrame, c: str, p: "CompParams", cache: dict) -> tuple[np.ndarray, np.ndarray]:
    """Shrunk points per opportunity and the shrinkage share."""
    opp = COMPONENTS[c]
    s_opp, s_pts = _dsum(d, opp, p.hl_eff, cache), _dsum(d, f"pts_{c}", p.hl_eff, cache)
    if ("mu", c) not in cache:
        cache[("mu", c)] = league_rate(d, f"pts_{c}", opp).to_numpy()
    mu = cache[("mu", c)]
    if p.k > 0:
        eff, shrink = (s_pts + p.k * mu) / (s_opp + p.k), p.k / (s_opp + p.k)
    else:
        eff, shrink = np.where(s_opp > 0, s_pts / np.where(s_opp > 0, s_opp, 1), mu), np.zeros(len(d))
    return eff, shrink


def project(games: pd.DataFrame, params: dict = DEFAULT_PARAMS, sums_cache: dict | None = None) -> pd.DataFrame:
    """Add projection columns. `games` must be sorted by player_id, season, week.

    Adds per component c: vol_c, eff_c, shrink_c, proj_c; plus proj_other and proj (total).
    sums_cache lets a parameter search reuse decayed sums (only with the same `games`).
    """
    d = add_components(games) if "pts_rec" not in games else games.copy()
    cache = {} if sums_cache is None else sums_cache
    total = np.zeros(len(d))
    for c in COMPONENTS:
        vol, eff, shrink = component_arrays(d, c, params[c], cache)
        d[f"vol_{c}"], d[f"eff_{c}"], d[f"shrink_{c}"], d[f"proj_{c}"] = vol, eff, shrink, vol * eff
        total = total + vol * eff
    h = params["other_hl"]
    w = _dsum(d, None, h, cache)
    d["proj_other"] = np.where(w > 0, _dsum(d, "pts_other", h, cache) / np.where(w > 0, w, 1), np.nan)
    d["proj"] = total + d["proj_other"].to_numpy()
    return d
