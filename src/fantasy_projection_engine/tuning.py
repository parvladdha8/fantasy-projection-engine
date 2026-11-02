"""Choose model settings using ONLY the seasons we pass in.

Used two ways:
  * on all dev seasons, to report the final settings
  * inside forward-chaining validation: to score season s, tune on seasons < s only.
"""

import itertools

import numpy as np
import pandas as pd

from .baseline import METHODS, RELEVANT_SLOTS, add_projection, big60_pool, score
from .opp_eff import COMPONENTS, DEFAULT_PARAMS, CompParams, component_arrays, project

HL_VOL = [1, 2, 3, 4, 6, 8, 12]
HL_EFF = [2, 3, 4, 6, 8, 12, 16, 32, 64]
K = [0, 10, 25, 50, 100, 200, 400, 800]
HL_OTHER = [8, 16, 32, 64, 128]
# Volume shrinkage (v2). (hl_long, m) pairs; m = 0 is v1, so v2's grid nests v1's.
VOL_SHRINK_V1 = [(64, 0)]
HL_TEAM = [4, 8, 16, 32, 64]  # team-volume memory searched when team context is on (v3)
VOL_SHRINK_V2 = [(64, 0)] + [(hl, m) for hl in (8, 16, 32, 64) for m in (1, 2, 4, 8)]


def relevant_mask(g: pd.DataFrame) -> np.ndarray:
    """Fantasy-relevant player-games: weekly top 15 QB / 30 RB / 30 WR / 15 TE by the
    fixed EWMA-hl8 baseline's PRE-GAME projection. No outcome information is used."""
    p = add_projection(g, "ewma_hl8", "_proj_rel")
    return g.index.isin(big60_pool(p, "_proj_rel", RELEVANT_SLOTS).index)


def tune_opp_eff(g: pd.DataFrame, seasons: list[int], cache: dict | None = None,
                 vol_shrink=VOL_SHRINK_V1, row_mask: np.ndarray | None = None,
                 k_grid: list[float] = K, team: bool = False, lines: bool = False,
                 team_reg: bool = False) -> tuple[dict, dict]:
    """Per component, pick (hl_vol, hl_eff, k, hl_long, m) minimising that component's MSE on `seasons`.

    row_mask: optionally restrict the tuning loss to these rows (e.g. relevant_mask(g)).
    k_grid: efficiency-shrinkage values to search ([0] = no efficiency shrinkage).
    team: if True, volume = share × expected team volume (v3), searching HL_TEAM.
          grid_results rows then also carry hl_team at the end.
    lines: if True (with team=True), team volume also uses betting lines (v4).

    Returns (params, grid_results) where grid_results[c] = sorted list of (mse, hl_vol, hl_eff, k, hl_long, m).
    `g` must already have components (opp_eff.add_components).
    """
    cache = {} if cache is None else cache
    rows = g["season"].isin(seasons).to_numpy()
    if row_mask is not None:
        rows = rows & row_mask
    params, grid = dict(DEFAULT_PARAMS), {}
    actual = {c: g[f"pts_{c}"].to_numpy(float) for c in COMPONENTS}
    for c in COMPONENTS:
        res = []
        for hv, he, k, (hl, vm), ht in itertools.product(HL_VOL, HL_EFF, k_grid, vol_shrink, HL_TEAM if team else [8]):
            vol, eff, _ = component_arrays(g, c, CompParams(hv, he, k, hl, vm, team, ht, lines, team_reg), cache)
            pred = vol * eff
            m = rows & ~np.isnan(pred)
            res.append((float(np.mean((actual[c][m] - pred[m]) ** 2)), hv, he, k, hl, vm, ht))
        res.sort()
        grid[c] = res
        best = res[0]
        params[c] = CompParams(*best[1:6], team=team, hl_team=best[6], lines=lines, team_reg=team_reg)
    oth = []
    for h in HL_OTHER:
        p = project(g, {**DEFAULT_PARAMS, "other_hl": h}, cache)
        m = rows & p["proj_other"].notna().to_numpy()
        oth.append((float(np.mean((p.loc[m, "pts_other"] - p.loc[m, "proj_other"]) ** 2)), h))
    params["other_hl"] = min(oth)[1]
    grid["other"] = sorted(oth)
    return params, grid


def tune_baseline(g: pd.DataFrame, seasons: list[int]) -> str:
    """Pick the baseline averaging method with lowest Big-60 MAE on `seasons`."""
    best = None
    for m in METHODS:
        p = add_projection(g, m)
        v = score(big60_pool(p[p["season"].isin(seasons)]))["mae"]
        if best is None or v < best[0]:
            best = (v, m)
    return best[1]
