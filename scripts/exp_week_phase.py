"""Experiment: week-of-season effect (v6) vs position-only recalibration (v6-pos). Dev seasons only.

Pre-registered (DECISIONS.md, 2026-11-02):
  v6     = v5 × (1 + γ[position, phase]), phases wk 1–4 / 5–12 / 13–18, EB-shrunk toward position γ
  v6pos  = v5 × (1 + γ[position])        (control)
  γ fitted walk-forward on fantasy-relevant player-games, seasons 2019..s−1.
  Headline: v6 vs v6pos. Adopt only if p < 0.05 AND v6 beats v5.

Usage: uv run python scripts/exp_week_phase.py
"""

import numpy as np
import pandas as pd

from fantasy_projection_engine import DEV_SEASONS
from fantasy_projection_engine.baseline import add_projection, big60_pool
from fantasy_projection_engine.data import PROJECT_ROOT
from fantasy_projection_engine.metrics import mae, paired_bootstrap
from fantasy_projection_engine.opp_eff import project
from fantasy_projection_engine.situational import week_multiplier
from fantasy_projection_engine.tuning import VOL_SHRINK_V2, relevant_mask, tune_baseline, tune_opp_eff

from exp_betting_lines import fmt, load_games
from exp_eff_lines import with_eff_adj

MODELS = ["base", "v5", "v6pos", "v6"]
COMPARE = [("v6", "v6pos"), ("v6", "v5"), ("v6pos", "v5"), ("v6", "base")]


def main():
    g = load_games()
    rel = relevant_mask(g)
    cache, folds, settings, tables = {}, [], [], []
    for s in DEV_SEASONS[1:]:
        train = [t for t in DEV_SEASONS if t < s]
        fold = add_projection(g, tune_baseline(g, train), "proj_base")
        v4, _ = tune_opp_eff(g, train, cache, VOL_SHRINK_V2, rel, team=True, lines=True)
        settings.append(f"| {s} | {fmt(v4)} |")
        fold["proj_v5"] = project(g, with_eff_adj(v4, "lines"), cache)["proj"].to_numpy()
        for name, mode in [("v6pos", "pos"), ("v6", "phase")]:
            mult, t = week_multiplier(fold, "proj_v5", rel, mode)
            fold[f"proj_{name}"] = fold["proj_v5"] * mult
            if mode == "phase":
                tables.append(t[t["season"] == s])
        folds.append(fold[fold["season"] == s])
    df = pd.concat(folds, ignore_index=True).dropna(subset=[f"proj_{m}" for m in MODELS])
    df["cluster"] = df["season"].astype(str) + "-" + df["week"].astype(str)
    idx = big60_pool(df, "proj_base").index
    for m in MODELS[1:]:
        idx = idx.union(big60_pool(df, f"proj_{m}").index)
    big = df.loc[idx]
    tab = pd.concat(tables, ignore_index=True)

    L = ["# Experiment: week-of-season effect (v6), forward-chained OOS 2020–2023", "",
         "## v5 settings per fold (hl_vol/hl_eff/k/hl_long/m/hl_team)", "",
         "| season | rec | rush | pass |", "|---|---|---|---|", *settings, "",
         "## Fitted week-of-season effects (from seasons 2019..s−1; γ = % over/under-scoring vs v5)", "",
         "| season | position | phase | raw γ | se | shrinkage B | shrunk γ |", "|---|---|---|---|---|---|---|"]
    L += [f"| {r.season} | {r.position} | {r.phase} | {100*r.raw:+.1f}% | {100*r.se:.1f}% | {r.B:.2f} | {100*r.gamma:+.1f}% |"
          for r in tab.sort_values(["season", "position", "phase"]).itertuples()]
    L += ["", "## Results (Big-60 = union of all four models' pools)", "",
          "| pool | A vs B | n | MAE A | MAE B | diff (A−B) | 95% CI | p(A not better) |", "|---|---|---|---|---|---|---|---|"]
    for name, d in {"big60": big, "all": df, "big60 weeks 13–18 (descriptive)": big[big.week >= 13]}.items():
        for a, b in COMPARE:
            r = paired_bootstrap((d["actual"] - d[f"proj_{a}"]).abs(), (d["actual"] - d[f"proj_{b}"]).abs(), d["cluster"])
            L.append(f"| {name} | {a} vs {b} | {len(d)} | {mae(d['actual'], d[f'proj_{a}']):.3f} | {mae(d['actual'], d[f'proj_{b}']):.3f} | "
                     f"{r['diff']:+.3f} | [{r['ci_low']:+.3f}, {r['ci_high']:+.3f}] | {r['p_a_not_better']:.3f} |")
    L += ["", "## Big-60 bias by phase (mean projection − actual)", "", "| model | early | mid | late |", "|---|---|---|---|"]
    ph = pd.cut(big["week"], [0, 4, 12, 99], labels=["early", "mid", "late"])
    for m in MODELS:
        L.append(f"| {m} | " + " | ".join(f"{(big[f'proj_{m}'] - big['actual'])[ph == p].mean():+.2f}" for p in ["early", "mid", "late"]) + " |")
    (PROJECT_ROOT / "reports" / "exp_week_phase.md").write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
