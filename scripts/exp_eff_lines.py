"""Experiment: betting lines for EFFICIENCY (v5) vs the α-only control (v5-cal). Dev seasons only.

Pre-registered (DECISIONS.md, 2026-11-02):
  v5     = v4 with efficiency × (1 + α + β·(implied − ī)), fitted walk-forward by season
  v5cal  = v4 with efficiency × (1 + α)          (control: calibration only, no lines)
  Settings (half-lives, k, m) tuned exactly as v4 per fold; the multiplier is fitted afterwards.
  Headline: v5 vs v5cal. Adopt v5 only if p < 0.05 AND v5 beats v4.

Usage: uv run python scripts/exp_eff_lines.py
"""

from dataclasses import replace

import numpy as np
import pandas as pd

from fantasy_projection_engine import DEV_SEASONS
from fantasy_projection_engine.baseline import add_projection, big60_pool
from fantasy_projection_engine.data import PROJECT_ROOT
from fantasy_projection_engine.metrics import mae, paired_bootstrap
from fantasy_projection_engine.opp_eff import COMPONENTS, project
from fantasy_projection_engine.tuning import VOL_SHRINK_V2, relevant_mask, tune_baseline, tune_opp_eff

from exp_betting_lines import fmt, load_games

MODELS = ["base", "v4", "v5cal", "v5"]
COMPARE = [("v5", "v5cal"), ("v5", "v4"), ("v5cal", "v4"), ("v5", "base")]


def with_eff_adj(params, mode):
    return {c: (replace(p, eff_adj=mode) if c in COMPONENTS else p) for c, p in params.items()}


def main():
    g = load_games()
    rel = relevant_mask(g)
    cache, folds, settings, coefs = {}, [], [], []
    for s in DEV_SEASONS[1:]:
        train = [t for t in DEV_SEASONS if t < s]
        fold = add_projection(g, tune_baseline(g, train), "proj_base")
        v4, _ = tune_opp_eff(g, train, cache, VOL_SHRINK_V2, rel, team=True, lines=True)
        settings.append(f"| {s} | v4 (= v5 settings) | {fmt(v4)} |")
        for name, p in {"v4": v4, "v5cal": with_eff_adj(v4, "cal"), "v5": with_eff_adj(v4, "lines")}.items():
            out = project(g, p, cache)
            fold[f"proj_{name}"] = out["proj"].to_numpy()
            if name == "v5":
                here = out["season"] == s
                for c in COMPONENTS:
                    mult = out.loc[here, f"eff_{c}"] / project(g, v4, cache).loc[here, f"eff_{c}"]
                    ok = np.isfinite(mult)
                    slope, icpt = np.polyfit(out.loc[here, "implied"][ok], mult[ok], 1)
                    coefs.append(f"| {s} | {c} | {100 * slope:+.2f}% | {mult[ok].mean():.3f} |")
        folds.append(fold[fold["season"] == s])
    df = pd.concat(folds, ignore_index=True).dropna(subset=[f"proj_{m}" for m in MODELS])
    df["cluster"] = df["season"].astype(str) + "-" + df["week"].astype(str)
    idx = big60_pool(df, "proj_base").index
    for m in MODELS[1:]:
        idx = idx.union(big60_pool(df, f"proj_{m}").index)
    big = df.loc[idx]

    L = ["# Experiment: betting lines for efficiency (v5), forward-chained OOS 2020–2023", "",
         "## Settings per fold (hl_vol/hl_eff/k/hl_long/m/hl_team)", "",
         "| season | model | rec | rush | pass |", "|---|---|---|---|---|", *settings, "",
         "## Fitted environment effect (coefficients from seasons < s)", "",
         "| season | component | β: change in points/opportunity per +1 implied point | mean multiplier (1 + α) |",
         "|---|---|---|---|", *coefs, "",
         "## Results (Big-60 = union of all four models' pools)", "",
         "| pool | A vs B | n | MAE A | MAE B | diff (A−B) | 95% CI | p(A not better) |", "|---|---|---|---|---|---|---|---|"]
    for name, d in {"big60": big, "all": df}.items():
        for a, b in COMPARE:
            r = paired_bootstrap((d["actual"] - d[f"proj_{a}"]).abs(), (d["actual"] - d[f"proj_{b}"]).abs(), d["cluster"])
            L.append(f"| {name} | {a} vs {b} | {len(d)} | {mae(d['actual'], d[f'proj_{a}']):.3f} | {mae(d['actual'], d[f'proj_{b}']):.3f} | "
                     f"{r['diff']:+.3f} | [{r['ci_low']:+.3f}, {r['ci_high']:+.3f}] | {r['p_a_not_better']:.3f} |")
    L += ["", "## Big-60 MAE by position (descriptive)", "", "| model | QB | RB | WR | TE |", "|---|---|---|---|---|"]
    for m in MODELS:
        L.append(f"| {m} | " + " | ".join(f"{mae(big.loc[big.position == p, 'actual'], big.loc[big.position == p, f'proj_{m}']):.3f}"
                                         for p in ["QB", "RB", "WR", "TE"]) + " |")
    L += ["", "## Bias in Big-60 pool", "", "| " + " | ".join(MODELS) + " |", "|" + "---|" * len(MODELS),
          "| " + " | ".join(f"{np.mean(big[f'proj_{m}'] - big['actual']):+.2f}" for m in MODELS) + " |"]
    (PROJECT_ROOT / "reports" / "exp_eff_lines.md").write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
