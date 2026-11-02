"""Experiment: team context (v3: share × expected team volume) vs current v2. Dev seasons only.

Pre-registered (DECISIONS.md, 2026-11-01): same framework as the paper ablation —
relevant-player tuning loss, wide grid (+ team-volume half-life 4–64), forward-chaining
OOS 2020–2023, Big-60 union pool, paired week-clustered bootstrap.
Headline test: v3 vs v2. Secondary: v3 vs baseline.

Usage: uv run python scripts/exp_team_context.py
"""

import numpy as np
import pandas as pd

from fantasy_projection_engine import DEV_SEASONS
from fantasy_projection_engine.baseline import add_projection, big60_pool, prepare_games
from fantasy_projection_engine.data import PROJECT_ROOT, load_player_stats, load_players, load_snap_counts
from fantasy_projection_engine.metrics import mae, paired_bootstrap
from fantasy_projection_engine.opp_eff import COMPONENTS, add_components, project
from fantasy_projection_engine.player_games import build_player_games
from fantasy_projection_engine.team_context import add_team_totals, build_team_games
from fantasy_projection_engine.tuning import VOL_SHRINK_V2, relevant_mask, tune_baseline, tune_opp_eff

MODELS = ["base", "v2", "v3"]


def fmt(p):
    return " | ".join(
        f"{p[c].hl_vol}/{p[c].hl_eff}/{p[c].k}/{p[c].hl_long if p[c].m else '–'}/{p[c].m}/{p[c].hl_team if p[c].team else '–'}"
        for c in COMPONENTS)


def main():
    ps = load_player_stats()
    pg = add_team_totals(build_player_games(ps, load_snap_counts(), load_players()), build_team_games(ps))
    g = add_components(prepare_games(pg))
    rel = relevant_mask(g)
    cache, folds, settings = {}, [], []
    for s in DEV_SEASONS[1:]:
        train = [t for t in DEV_SEASONS if t < s]
        fold = add_projection(g, tune_baseline(g, train), "proj_base")
        for name, team in [("v2", False), ("v3", True)]:
            params, _ = tune_opp_eff(g, train, cache, VOL_SHRINK_V2, rel, team=team)
            proj = project(g, params, cache)
            fold[f"proj_{name}"] = proj["proj"].to_numpy()
            if name == "v3":
                fold["vol_rec_v3"] = proj["vol_rec"].to_numpy()
            settings.append(f"| {s} | {name} | {fmt(params)} |")
        folds.append(fold[fold["season"] == s])
    df = pd.concat(folds, ignore_index=True).dropna(subset=[f"proj_{m}" for m in MODELS])
    df["cluster"] = df["season"].astype(str) + "-" + df["week"].astype(str)
    idx = big60_pool(df, "proj_base").index
    for m in MODELS[1:]:
        idx = idx.union(big60_pool(df, f"proj_{m}").index)
    big = df.loc[idx]

    L = ["# Experiment: team context (v3) vs v2, forward-chained OOS 2020–2023", "",
         "## Settings per fold (hl_vol/hl_eff/k/hl_long/m/hl_team)", "",
         "| season | model | rec | rush | pass |", "|---|---|---|---|---|", *settings, "",
         "## Results (Big-60 = union of all three models' pools)", "",
         "| pool | A vs B | n | MAE A | MAE B | diff (A−B) | 95% CI | p(A not better) |", "|---|---|---|---|---|---|---|---|"]
    for name, d in {"big60": big, "all": df}.items():
        for a, b in [("v3", "v2"), ("v3", "base"), ("v2", "base")]:
            r = paired_bootstrap((d["actual"] - d[f"proj_{a}"]).abs(), (d["actual"] - d[f"proj_{b}"]).abs(), d["cluster"])
            L.append(f"| {name} | {a} vs {b} | {len(d)} | {mae(d['actual'], d[f'proj_{a}']):.3f} | {mae(d['actual'], d[f'proj_{b}']):.3f} | "
                     f"{r['diff']:+.3f} | [{r['ci_low']:+.3f}, {r['ci_high']:+.3f}] | {r['p_a_not_better']:.3f} |")
    L += ["", "## Big-60 MAE by position (descriptive)", "", "| model | QB | RB | WR | TE |", "|---|---|---|---|---|"]
    for m in MODELS:
        L.append(f"| {m} | " + " | ".join(f"{mae(big.loc[big.position == p, 'actual'], big.loc[big.position == p, f'proj_{m}']):.3f}"
                                         for p in ["QB", "RB", "WR", "TE"]) + " |")
    L += ["", "## Bias in Big-60 pool", "", "| base | v2 | v3 |", "|---|---|---|",
          "| " + " | ".join(f"{np.mean(big[f'proj_{m}'] - big['actual']):+.2f}" for m in MODELS) + " |"]
    out = PROJECT_ROOT / "reports" / "exp_team_context.md"
    out.write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
