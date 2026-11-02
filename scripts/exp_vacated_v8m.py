"""One pre-specified re-test: vacated opportunity on top of the median calibration (v7m vs v8m). Dev only.

Pre-registered (DECISIONS.md, 2026-11-02):
  v8m          = v5 → percentage-only median map
  v7m          = v5 + vacated opportunity → percentage-only median map (fitted on v7's projections)
  v7m-placebo  = same with absences moved to random teams in the same week
  Adopt only if v7m vs v8m p < 0.05, placebo vs v8m NOT significantly better, and v7m vs placebo p < 0.05.

Usage: uv run python scripts/exp_vacated_v8m.py
"""

import numpy as np
import pandas as pd

from fantasy_projection_engine import DEV_SEASONS
from fantasy_projection_engine.baseline import add_projection, big60_pool
from fantasy_projection_engine.calibration import median_calibration
from fantasy_projection_engine.data import PROJECT_ROOT, load_injuries, load_schedules
from fantasy_projection_engine.injuries import build_absences, link_absences
from fantasy_projection_engine.metrics import mae, paired_bootstrap, rmse
from fantasy_projection_engine.opp_eff import project
from fantasy_projection_engine.tuning import VOL_SHRINK_V2, relevant_mask, tune_baseline, tune_opp_eff

from exp_betting_lines import load_games
from exp_eff_lines import with_eff_adj
from exp_vacated import placebo_links, with_vacated

MODELS = ["base", "v8m", "v7m_placebo", "v7m"]
COMPARE = [("v7m", "v8m"), ("v7m_placebo", "v8m"), ("v7m", "v7m_placebo"), ("v7m", "base")]


def main():
    g = load_games()
    rel = relevant_mask(g)
    cache, folds = {}, []
    cache[("links", "real")] = link_absences(g, build_absences(load_injuries(), load_schedules()))
    cache[("links", "placebo")] = placebo_links(cache[("links", "real")], g)
    for s in DEV_SEASONS[1:]:
        train = [t for t in DEV_SEASONS if t < s]
        fold = add_projection(g, tune_baseline(g, train), "proj_base")
        v4, _ = tune_opp_eff(g, train, cache, VOL_SHRINK_V2, rel, team=True, lines=True)
        v5 = with_eff_adj(v4, "lines")
        fold["raw_v8m"] = project(g, v5, cache)["proj"].to_numpy()
        for name, tag in [("v7m", "real"), ("v7m_placebo", "placebo")]:
            fold[f"raw_{name}"] = project(g, with_vacated(v5), cache, absence_tag=tag)["proj"].to_numpy()
        for name in MODELS[1:]:
            fold[f"proj_{name}"] = median_calibration(fold, f"raw_{name}", rel, "lad_mult")[0]
        folds.append(fold[fold["season"] == s])
    df = pd.concat(folds, ignore_index=True).dropna(subset=[f"proj_{m}" for m in MODELS])
    df["cluster"] = df["season"].astype(str) + "-" + df["week"].astype(str)
    idx = big60_pool(df, "proj_base").index
    for m in MODELS[1:]:
        idx = idx.union(big60_pool(df, f"proj_{m}").index)
    big = df.loc[idx]
    L = ["# Re-test: vacated opportunity on top of median calibration (v7m vs v8m), OOS 2020–2023", "",
         "| pool | A vs B | n | MAE A | MAE B | diff (A−B) | 95% CI | p(A not better) |", "|---|---|---|---|---|---|---|---|"]
    for name, d in {"big60": big, "all": df}.items():
        for a, b in COMPARE:
            r = paired_bootstrap((d["actual"] - d[f"proj_{a}"]).abs(), (d["actual"] - d[f"proj_{b}"]).abs(), d["cluster"])
            L.append(f"| {name} | {a} vs {b} | {len(d)} | {mae(d['actual'], d[f'proj_{a}']):.3f} | {mae(d['actual'], d[f'proj_{b}']):.3f} | "
                     f"{r['diff']:+.3f} | [{r['ci_low']:+.3f}, {r['ci_high']:+.3f}] | {r['p_a_not_better']:.3f} |")
    L += ["", "## Big-60 summary", "", "| model | MAE | RMSE | median error |", "|---|---|---|---|"]
    for m in MODELS:
        L.append(f"| {m} | {mae(big['actual'], big[f'proj_{m}']):.3f} | {rmse(big['actual'], big[f'proj_{m}']):.3f} | "
                 f"{(big[f'proj_{m}'] - big['actual']).median():+.2f} |")
    (PROJECT_ROOT / "reports" / "exp_vacated_v8m.md").write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
