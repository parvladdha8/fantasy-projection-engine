"""Experiment: tune on fantasy-relevant players only (option A). Dev seasons only.

Pre-registered plan (DECISIONS.md, 2026-11-01):
  relevant = weekly top 15 QB / 30 RB / 30 WR / 15 TE by the fixed EWMA-hl8 baseline's pre-game projection
  wide grid; forward-chaining OOS (score s, tune on dev seasons < s); paired week-clustered bootstrap.

Models:
  base    trailing-average baseline (method tuned per fold)
  v2_all  OE with volume shrinkage, tuned on all players (previous run)
  v1_rel  OE without volume shrinkage, tuned on relevant players
  v2_rel  OE with volume shrinkage, tuned on relevant players

Usage: uv run python scripts/exp_tuning_target.py
"""

import numpy as np
import pandas as pd

from fantasy_projection_engine import DEV_SEASONS
from fantasy_projection_engine.baseline import add_projection, big60_pool, prepare_games
from fantasy_projection_engine.data import PROJECT_ROOT, load_player_stats, load_players, load_snap_counts
from fantasy_projection_engine.metrics import mae, paired_bootstrap
from fantasy_projection_engine.opp_eff import COMPONENTS, add_components, project
from fantasy_projection_engine.player_games import build_player_games
from fantasy_projection_engine.tuning import VOL_SHRINK_V1, VOL_SHRINK_V2, relevant_mask, tune_baseline, tune_opp_eff

KEY = ["player_id", "season", "week"]
MODELS = ["base", "v2_all", "v1_rel", "v2_rel"]
COMPARISONS = [("v2_rel", "base"), ("v2_rel", "v2_all"), ("v2_rel", "v1_rel"), ("v1_rel", "base")]


def fmt(p):
    return " | ".join(f"{p[c].hl_vol}/{p[c].hl_eff}/{p[c].k}/{p[c].hl_long if p[c].m else '–'}/{p[c].m}" for c in COMPONENTS)


def main():
    g = add_components(prepare_games(build_player_games(load_player_stats(), load_snap_counts(), load_players())))
    rel = relevant_mask(g)
    cache, folds, settings = {}, [], []
    for s in DEV_SEASONS[1:]:
        train = [t for t in DEV_SEASONS if t < s]
        params = {
            "v2_all": tune_opp_eff(g, train, cache, VOL_SHRINK_V2)[0],
            "v1_rel": tune_opp_eff(g, train, cache, VOL_SHRINK_V1, rel)[0],
            "v2_rel": tune_opp_eff(g, train, cache, VOL_SHRINK_V2, rel)[0],
        }
        fold = add_projection(g, tune_baseline(g, train), "proj_base")
        for name, p in params.items():
            fold[f"proj_{name}"] = project(g, p, cache)["proj"].to_numpy()
            settings.append(f"| {s} | {name} | {fmt(p)} |")
        folds.append(fold[fold["season"] == s])
    df = pd.concat(folds, ignore_index=True).dropna(subset=[f"proj_{m}" for m in MODELS])
    df["cluster"] = df["season"].astype(str) + "-" + df["week"].astype(str)
    idx = big60_pool(df, "proj_base").index
    for m in MODELS[1:]:
        idx = idx.union(big60_pool(df, f"proj_{m}").index)
    big = df.loc[idx]

    lines = ["# Experiment: tuning target = fantasy-relevant players (option A), OOS 2020–2023", "",
             "## Settings per fold (hl_vol/hl_eff/k/hl_long/m)", "",
             "| season | model | rec | rush | pass |", "|---|---|---|---|---|", *settings, "",
             "## Results (Big-60 = union of all models' own pools)", "",
             "| pool | A vs B | n | MAE A | MAE B | diff (A−B) | 95% CI | p(A not better) |",
             "|---|---|---|---|---|---|---|---|"]
    pools = {"big60": big, "all": df, **{f"big60 {p}": big[big["position"] == p] for p in ["QB", "RB", "WR", "TE"]}}
    for name, d in pools.items():
        for a, b in COMPARISONS:
            if name.startswith("big60 ") and (a, b) != ("v2_rel", "base"):
                continue  # per-position: headline comparison only (limits multiple testing)
            r = paired_bootstrap((d["actual"] - d[f"proj_{a}"]).abs(), (d["actual"] - d[f"proj_{b}"]).abs(), d["cluster"])
            lines.append(f"| {name} | {a} vs {b} | {len(d)} | {mae(d['actual'], d[f'proj_{a}']):.3f} | "
                         f"{mae(d['actual'], d[f'proj_{b}']):.3f} | {r['diff']:+.3f} | "
                         f"[{r['ci_low']:+.3f}, {r['ci_high']:+.3f}] | {r['p_a_not_better']:.3f} |")
    lines += ["", "## Bias in Big-60 pool (mean projection − actual)", "",
              "| " + " | ".join(MODELS) + " |", "|" + "---|" * len(MODELS),
              "| " + " | ".join(f"{np.mean(big[f'proj_{m}'] - big['actual']):+.2f}" for m in MODELS) + " |"]
    out = PROJECT_ROOT / "reports" / "exp_tuning_target.md"
    out.write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
