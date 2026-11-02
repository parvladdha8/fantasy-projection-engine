"""Choose model settings using ONLY the seasons we pass in.

Used two ways:
  * on all dev seasons, to report the final settings
  * inside forward-chaining validation: to score season s, tune on seasons < s only.
"""

import itertools

import numpy as np
import pandas as pd

from .baseline import METHODS, add_projection, big60_pool, score
from .opp_eff import COMPONENTS, DEFAULT_PARAMS, CompParams, project

HL_VOL = [2, 3, 4, 6, 8, 12]
HL_EFF = [2, 3, 4, 6, 8, 12, 16, 32, 64]
K = [0, 10, 25, 50, 100, 200, 400, 800]
HL_OTHER = [8, 16, 32, 64, 128]


def tune_opp_eff(g: pd.DataFrame, seasons: list[int], cache: dict | None = None) -> tuple[dict, dict]:
    """Per component, pick (hl_vol, hl_eff, k) minimising that component's MSE on `seasons`.

    Returns (params, grid_results) where grid_results[c] = sorted list of (mse, hl_vol, hl_eff, k).
    """
    cache = {} if cache is None else cache
    rows = g["season"].isin(seasons).to_numpy()
    params, grid = dict(DEFAULT_PARAMS), {}
    for c in COMPONENTS:
        res = []
        for hv, he, k in itertools.product(HL_VOL, HL_EFF, K):
            p = project(g, {**DEFAULT_PARAMS, c: CompParams(hv, he, k)}, cache)
            m = rows & p[f"proj_{c}"].notna().to_numpy()
            res.append((float(np.mean((p.loc[m, f"pts_{c}"] - p.loc[m, f"proj_{c}"]) ** 2)), hv, he, k))
        res.sort()
        grid[c] = res
        params[c] = CompParams(*res[0][1:])
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
