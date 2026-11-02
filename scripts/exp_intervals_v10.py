"""Experiment: floor/ceiling for all players + per-player spread (v10). Dev seasons only.

Pre-registered (DECISIONS.md, 2026-11-02):
  v10        q_τ = a + b·proj + c·proj·z   (per position, fitted on ALL player-games, walk-forward)
  v10novol   q_τ = a + b·proj              (control)
  v9         q_τ = b·proj, fitted on relevant players (current)
  Median = v8m for all three. Crossing fixed: floor = min(floor, median), ceiling = max(ceiling, median).

Usage: uv run python scripts/exp_intervals_v10.py
"""

import numpy as np
import pandas as pd

from fantasy_projection_engine import DEV_SEASONS
from fantasy_projection_engine.baseline import add_projection, big60_pool
from fantasy_projection_engine.calibration import median_calibration, quantile_band, shrunk_volatility
from fantasy_projection_engine.data import PROJECT_ROOT
from fantasy_projection_engine.metrics import coverage, interval_score, paired_bootstrap
from fantasy_projection_engine.opp_eff import project
from fantasy_projection_engine.tuning import VOL_SHRINK_V2, relevant_mask, tune_baseline, tune_opp_eff

from exp_betting_lines import load_games
from exp_eff_lines import with_eff_adj

BANDS = ["v9", "v10novol", "v10"]
COMPARE = [("v10", "v9"), ("v10novol", "v9"), ("v10", "v10novol")]


def cov_row(label, d, m):
    c = coverage(d["actual"], d[f"{m}_lo"], d[f"{m}_hi"])
    return f"| {label} | {m} | {len(d)} | {100 * c['inside']:.1f}% | {100 * c['below']:.1f}% | {100 * c['above']:.1f}% |"


def main():
    g = load_games()
    g["z"] = shrunk_volatility(g).to_numpy()
    rel = relevant_mask(g)
    every = np.ones(len(g), bool)
    cache, folds, coefs = {}, [], []
    for s in DEV_SEASONS[1:]:
        train = [t for t in DEV_SEASONS if t < s]
        fold = add_projection(g, tune_baseline(g, train), "proj_base")
        v4, _ = tune_opp_eff(g, train, cache, VOL_SHRINK_V2, rel, team=True, lines=True)
        fold["raw"] = project(g, with_eff_adj(v4, "lines"), cache)["proj"].to_numpy()
        fold["med"] = median_calibration(fold, "raw", rel, "lad_mult")[0]
        for k, tau in [("lo", 0.1), ("hi", 0.9)]:
            fold[f"v9_{k}"] = median_calibration(fold, "raw", rel, "lad_mult", tau=tau)[0]
            fold[f"v10novol_{k}"] = quantile_band(fold, "raw", None, every, tau)[0]
            fold[f"v10_{k}"], t = quantile_band(fold, "raw", "z", every, tau)
            coefs += [f"| {s} | {r.position} | {k} | {r.a:+.2f} | {r.b:.3f} | {r.c:+.3f} |" for r in t[t.season == s].itertuples()]
        for m in BANDS:
            fold[f"{m}_lo"] = np.minimum(fold[f"{m}_lo"], fold["med"])
            fold[f"{m}_hi"] = np.maximum(fold[f"{m}_hi"], fold["med"])
        folds.append(fold[fold["season"] == s])
    cols = ["med"] + [f"{m}_{k}" for m in BANDS for k in ("lo", "hi")]
    df = pd.concat(folds, ignore_index=True).dropna(subset=cols)
    df["cluster"] = df["season"].astype(str) + "-" + df["week"].astype(str)
    big = df.loc[big60_pool(df, "proj_base").index.union(big60_pool(df, "med").index)].copy()
    for d in (big, df):
        for m in BANDS:
            d[f"is_{m}"] = interval_score(d["actual"], d[f"{m}_lo"], d[f"{m}_hi"])

    L = ["# Experiment: floor/ceiling for all players + per-player spread (v10), OOS 2020–2023", "",
         "## Fitted quantile maps, v10 (q = a + b·proj + c·proj·z; z = shrunk volatility vs position average)", "",
         "| season | position | quantile | a | b | c |", "|---|---|---|---|---|---|", *coefs, "",
         "## Calibration (target 80% inside, 10% / 10%)", "",
         "| pool | model | n | inside | below floor | above ceiling |", "|---|---|---|---|---|---|"]
    for label, d in [("**Big-60**", big), ("**All players**", df)]:
        L += [cov_row(label, d, m) for m in BANDS]
    for p in ["QB", "RB", "WR", "TE"]:
        L += [cov_row(f"Big-60 {p}", big[big.position == p], m) for m in ("v9", "v10")]
        L += [cov_row(f"All {p}", df[df.position == p], m) for m in ("v9", "v10")]
    terc = pd.qcut(big["z"].rank(method="first"), 3, labels=["steady", "middle", "volatile"])
    for t in terc.cat.categories:
        L += [cov_row(f"Big-60 {t}", big[terc == t], m) for m in BANDS]
    dec = pd.qcut(df["med"].rank(method="first"), 10, labels=[f"D{i}" for i in range(1, 11)])
    L += ["", "## All players by projection decile (D1 = lowest projections)", "",
          "| decile | median proj | v9 inside | v10 inside | v10 below | v10 above |", "|---|---|---|---|---|---|"]
    for t in dec.cat.categories:
        d = df[dec == t]
        c9, c10 = coverage(d.actual, d.v9_lo, d.v9_hi), coverage(d.actual, d.v10_lo, d.v10_hi)
        L.append(f"| {t} | {d.med.median():.1f} | {100 * c9['inside']:.0f}% | {100 * c10['inside']:.0f}% | "
                 f"{100 * c10['below']:.0f}% | {100 * c10['above']:.0f}% |")
    L += ["", "## Interval score (lower = better; paired, week-clustered bootstrap)", "",
          "| pool | A vs B | n | A | B | diff | 95% CI | p(A not better) |", "|---|---|---|---|---|---|---|---|"]
    for name, d in {"big60": big, "all": df}.items():
        for a, b in COMPARE:
            r = paired_bootstrap(d[f"is_{a}"], d[f"is_{b}"], d["cluster"])
            L.append(f"| {name} | {a} vs {b} | {len(d)} | {d[f'is_{a}'].mean():.3f} | {d[f'is_{b}'].mean():.3f} | "
                     f"{r['diff']:+.3f} | [{r['ci_low']:+.3f}, {r['ci_high']:+.3f}] | {r['p_a_not_better']:.3f} |")
    L += ["", "## Average width (points)", "", "| pool | v9 | v10novol | v10 |", "|---|---|---|---|"]
    for name, d in {"Big-60": big, "All": df}.items():
        L.append(f"| {name} | " + " | ".join(f"{(d[f'{m}_hi'] - d[f'{m}_lo']).mean():.1f}" for m in BANDS) + " |")
    (PROJECT_ROOT / "reports" / "exp_intervals_v10.md").write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
