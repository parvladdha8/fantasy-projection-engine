"""Experiment: loss alignment, median calibration (v8) vs least-squares recalibration (v8-ols). Dev only.

Pre-registered (DECISIONS.md, 2026-11-02):
  v8     = a_pos + b_pos · proj_v5, fitted by least absolute deviations (median), walk-forward
  v8ols  = same map fitted by least squares (control)
  Adopt v8 if v8 vs v5 p < 0.05. Mechanism claim needs v8 vs v8ols p < 0.05 AND v8ols winning RMSE.

Usage: uv run python scripts/exp_median_cal.py
"""

import numpy as np
import pandas as pd

from fantasy_projection_engine import DEV_SEASONS
from fantasy_projection_engine.baseline import add_projection, big60_pool
from fantasy_projection_engine.calibration import median_calibration
from fantasy_projection_engine.data import PROJECT_ROOT
from fantasy_projection_engine.metrics import mae, paired_bootstrap, rmse
from fantasy_projection_engine.opp_eff import project
from fantasy_projection_engine.tuning import VOL_SHRINK_V2, relevant_mask, tune_baseline, tune_opp_eff

from exp_betting_lines import fmt, load_games
from exp_eff_lines import with_eff_adj

MODELS = ["base", "v5", "v8ols", "v8"]
COMPARE = [("v8", "v5"), ("v8", "v8ols"), ("v8ols", "v5"), ("v8", "base")]


def main():
    g = load_games()
    rel = relevant_mask(g)
    cache, folds, settings, coefs = {}, [], [], []
    for s in DEV_SEASONS[1:]:
        train = [t for t in DEV_SEASONS if t < s]
        fold = add_projection(g, tune_baseline(g, train), "proj_base")
        v4, _ = tune_opp_eff(g, train, cache, VOL_SHRINK_V2, rel, team=True, lines=True)
        settings.append(f"| {s} | {fmt(v4)} |")
        fold["proj_v5"] = project(g, with_eff_adj(v4, "lines"), cache)["proj"].to_numpy()
        for name, method in [("v8ols", "ols"), ("v8", "lad")]:
            fold[f"proj_{name}"], t = median_calibration(fold, "proj_v5", rel, method)
            coefs += [f"| {s} | {name} | {r.position} | {r.a:+.2f} | {r.b:.3f} | {r.a + 15 * r.b:.2f} |"
                      for r in t[t["season"] == s].itertuples()]
        folds.append(fold[fold["season"] == s])
    df = pd.concat(folds, ignore_index=True).dropna(subset=[f"proj_{m}" for m in MODELS])
    df["cluster"] = df["season"].astype(str) + "-" + df["week"].astype(str)
    idx = big60_pool(df, "proj_base").index
    for m in MODELS[1:]:
        idx = idx.union(big60_pool(df, f"proj_{m}").index)
    big = df.loc[idx]

    L = ["# Experiment: loss alignment, median calibration (v8), forward-chained OOS 2020–2023", "",
         "## v5 settings per fold (hl_vol/hl_eff/k/hl_long/m/hl_team)", "",
         "| season | rec | rush | pass |", "|---|---|---|---|", *settings, "",
         "## Fitted maps (from seasons 2019..s−1): calibrated = a + b · v5 projection", "",
         "| season | model | position | a | b | a v5 projection of 15 becomes |", "|---|---|---|---|---|---|", *coefs, "",
         "## Results (Big-60 = union of all four models' pools)", "",
         "| pool | A vs B | n | MAE A | MAE B | diff (A−B) | 95% CI | p(A not better) |", "|---|---|---|---|---|---|---|---|"]
    for name, d in {"big60": big, "all": df}.items():
        for a, b in COMPARE:
            r = paired_bootstrap((d["actual"] - d[f"proj_{a}"]).abs(), (d["actual"] - d[f"proj_{b}"]).abs(), d["cluster"])
            L.append(f"| {name} | {a} vs {b} | {len(d)} | {mae(d['actual'], d[f'proj_{a}']):.3f} | {mae(d['actual'], d[f'proj_{b}']):.3f} | "
                     f"{r['diff']:+.3f} | [{r['ci_low']:+.3f}, {r['ci_high']:+.3f}] | {r['p_a_not_better']:.3f} |")
    L += ["", "## Each loss rewards its own target (Big-60)", "", "| model | MAE | RMSE | bias (mean) | median error |", "|---|---|---|---|---|"]
    for m in MODELS:
        e = big[f"proj_{m}"] - big["actual"]
        L.append(f"| {m} | {mae(big['actual'], big[f'proj_{m}']):.3f} | {rmse(big['actual'], big[f'proj_{m}']):.3f} | {e.mean():+.2f} | {e.median():+.2f} |")
    L += ["", "## Big-60 MAE by position (descriptive)", "", "| model | QB | RB | WR | TE |", "|---|---|---|---|---|"]
    for m in MODELS:
        L.append(f"| {m} | " + " | ".join(f"{mae(big.loc[big.position == p, 'actual'], big.loc[big.position == p, f'proj_{m}']):.3f}"
                                         for p in ["QB", "RB", "WR", "TE"]) + " |")
    (PROJECT_ROOT / "reports" / "exp_median_cal.md").write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
