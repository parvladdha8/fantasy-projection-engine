"""Paper table: ablation of shrinkage in the opportunity × efficiency model.

All models evaluated identically:
  * forward-chaining out-of-sample: score season s ∈ 2020–2023, tune only on dev seasons < s
  * tuning loss on fantasy-relevant players (weekly top 15/30/30/15 by baseline pre-game projection)
  * same player-games; Big-60 pool = union of every model's own weekly top 10/20/20/10
  * paired week-clustered bootstrap (2,000 draws) for each model vs baseline

Usage: uv run python scripts/paper_shrinkage_table.py   ->  paper/results_shrinkage_ablation.md
"""

import numpy as np
import pandas as pd

from fantasy_projection_engine import DEV_SEASONS
from fantasy_projection_engine.baseline import add_projection, big60_pool, prepare_games
from fantasy_projection_engine.data import PROJECT_ROOT, load_player_stats, load_players, load_snap_counts
from fantasy_projection_engine.metrics import mae, paired_bootstrap, rmse
from fantasy_projection_engine.opp_eff import add_components, project
from fantasy_projection_engine.player_games import build_player_games
from fantasy_projection_engine.tuning import VOL_SHRINK_V1, VOL_SHRINK_V2, relevant_mask, tune_baseline, tune_opp_eff

MODELS = {
    "base": "Baseline: trailing weighted average of PPR points",
    "oe_none": "Opp × Eff, no shrinkage (k = 0, m = 0)",
    "oe_v1": "Opp × Eff, efficiency shrinkage only (pre-volume-shrinkage, v1)",
    "oe_v2": "Opp × Eff, efficiency + volume shrinkage (current, v2)",
}


def main():
    g = add_components(prepare_games(build_player_games(load_player_stats(), load_snap_counts(), load_players())))
    rel = relevant_mask(g)
    cache, folds = {}, []
    for s in DEV_SEASONS[1:]:
        train = [t for t in DEV_SEASONS if t < s]
        fold = add_projection(g, tune_baseline(g, train), "proj_base")
        for name, kw in {
            "oe_none": dict(vol_shrink=VOL_SHRINK_V1, k_grid=[0]),
            "oe_v1": dict(vol_shrink=VOL_SHRINK_V1),
            "oe_v2": dict(vol_shrink=VOL_SHRINK_V2),
        }.items():
            params, _ = tune_opp_eff(g, train, cache, row_mask=rel, **kw)
            fold[f"proj_{name}"] = project(g, params, cache)["proj"].to_numpy()
        folds.append(fold[fold["season"] == s])
    df = pd.concat(folds, ignore_index=True).dropna(subset=[f"proj_{m}" for m in MODELS])
    df["cluster"] = df["season"].astype(str) + "-" + df["week"].astype(str)
    idx = big60_pool(df, "proj_base").index
    for m in list(MODELS)[1:]:
        idx = idx.union(big60_pool(df, f"proj_{m}").index)
    big = df.loc[idx]

    def stats(d, m):
        a, p = d["actual"], d[f"proj_{m}"]
        return mae(a, p), rmse(a, p), float(a.rank().corr(p.rank())), float(np.mean(p - a))

    L = ["# Shrinkage ablation: opportunity × efficiency vs baseline", "",
         f"Out-of-sample, forward-chained, seasons 2020–2023 (tuned on 2019..s−1). "
         f"Big-60 pool n = {len(big):,} player-games; all-players n = {len(df):,}.", "",
         "## Main table", "",
         "| Model | All-players MAE | Big-60 MAE | Big-60 Δ vs baseline | 95% CI | p (not better) | Big-60 RMSE | Big-60 Spearman | Big-60 bias |",
         "|---|---|---|---|---|---|---|---|---|"]
    for m, label in MODELS.items():
        a_mae = mae(df["actual"], df[f"proj_{m}"])
        b_mae, b_rmse, b_rho, b_bias = stats(big, m)
        if m == "base":
            delta = ci = pv = "—"
        else:
            r = paired_bootstrap((big["actual"] - big[f"proj_{m}"]).abs(), (big["actual"] - big["proj_base"]).abs(), big["cluster"])
            delta, ci, pv = f"{r['diff']:+.3f}", f"[{r['ci_low']:+.3f}, {r['ci_high']:+.3f}]", f"{r['p_a_not_better']:.3f}"
        L.append(f"| {label} | {a_mae:.3f} | {b_mae:.3f} | {delta} | {ci} | {pv} | {b_rmse:.3f} | {b_rho:.3f} | {b_bias:+.2f} |")

    L += ["", "## Step-by-step contribution on the Big-60 (each row vs the row above)", "",
          "| Step | Δ MAE | 95% CI | p (not better) |", "|---|---|---|---|"]
    steps = [("oe_none", "base", "Split into opportunity × efficiency (no shrinkage)"),
             ("oe_v1", "oe_none", "+ efficiency shrinkage (empirical Bayes, k)"),
             ("oe_v2", "oe_v1", "+ volume shrinkage (m)")]
    for a, b, label in steps:
        r = paired_bootstrap((big["actual"] - big[f"proj_{a}"]).abs(), (big["actual"] - big[f"proj_{b}"]).abs(), big["cluster"])
        L.append(f"| {label} | {r['diff']:+.3f} | [{r['ci_low']:+.3f}, {r['ci_high']:+.3f}] | {r['p_a_not_better']:.3f} |")

    L += ["", "## Big-60 MAE by position", "", "| Model | QB | RB | WR | TE |", "|---|---|---|---|---|"]
    for m, label in MODELS.items():
        L.append(f"| {label} | " + " | ".join(f"{mae(big.loc[big.position == p, 'actual'], big.loc[big.position == p, f'proj_{m}']):.3f}"
                                            for p in ["QB", "RB", "WR", "TE"]) + " |")
    L += ["", "## Notes", "",
          "- Δ < 0 means lower error than the comparison model. CI = 95% paired bootstrap resampling whole season-weeks.",
          "- Bias = mean(projection − actual); positive = over-projection.",
          "- All model settings are re-tuned inside each fold on earlier seasons only; 2024 and 2025 are untouched.",
          "- Numbers differ slightly from earlier experiment reports because the Big-60 union pool here includes all four models.",
          "- Per-position values are descriptive; they are not individually significance-tested (multiple comparisons)."]
    out = PROJECT_ROOT / "paper" / "results_shrinkage_ablation.md"
    out.write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
