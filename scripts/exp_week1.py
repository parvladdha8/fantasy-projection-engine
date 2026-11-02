"""Experiment: Week 1 effect on the median projection (v11 position level, v11p player level). Dev seasons only.

Pre-registered (DECISIONS.md, 2026-11-02):
  v11   Week 1 median = v8m × (1 + γ_pos), γ_pos by LAD on earlier Week 1s, EB-shrunk toward 0
  v11p  v11 + player-specific deviation, partially pooled toward the position effect
  Headline: v11 vs v8m, Big-60 union, Week 1 only, paired bootstrap clustered by GAME. Adopt if p < 0.05.

Usage: uv run python scripts/exp_week1.py
"""

import numpy as np
import pandas as pd

from fantasy_projection_engine import DEV_SEASONS
from fantasy_projection_engine.baseline import add_projection, big60_pool
from fantasy_projection_engine.calibration import median_calibration, quantile_band, shrunk_volatility
from fantasy_projection_engine.data import PROJECT_ROOT
from fantasy_projection_engine.metrics import coverage, mae, paired_bootstrap
from fantasy_projection_engine.opp_eff import project
from fantasy_projection_engine.situational import week1_multiplier
from fantasy_projection_engine.tuning import VOL_SHRINK_V2, relevant_mask, tune_baseline, tune_opp_eff

from exp_betting_lines import load_games
from exp_eff_lines import with_eff_adj

MODELS = ["base", "v8m", "v11", "v11p"]
COMPARE = [("v11", "v8m"), ("v11p", "v11"), ("v11p", "v8m"), ("v11", "base")]
POS = ["QB", "RB", "WR", "TE"]


def main():
    g = load_games()
    g["z"] = shrunk_volatility(g).to_numpy()
    rel = relevant_mask(g)
    every = np.ones(len(g), bool)
    cache, folds, ptabs, pltabs = {}, [], [], []
    for s in DEV_SEASONS[1:]:
        train = [t for t in DEV_SEASONS if t < s]
        fold = add_projection(g, tune_baseline(g, train), "proj_base")
        v4, _ = tune_opp_eff(g, train, cache, VOL_SHRINK_V2, rel, team=True, lines=True)
        fold["raw"] = project(g, with_eff_adj(v4, "lines"), cache)["proj"].to_numpy()
        fold["proj_v8m"] = median_calibration(fold, "raw", rel, "lad_mult")[0]
        m11, pt, _ = week1_multiplier(fold, "proj_v8m", rel)
        m11p, _, pl = week1_multiplier(fold, "proj_v8m", rel, player_level=True)
        fold["proj_v11"], fold["proj_v11p"] = fold["proj_v8m"] * m11, fold["proj_v8m"] * m11p
        for k, tau in [("lo", 0.1), ("hi", 0.9)]:
            fold[k] = quantile_band(fold, "raw", "z", every, tau)[0]
        fold["lo"], fold["hi"] = np.fmin(fold["lo"], fold["proj_v8m"]), np.fmax(fold["hi"], fold["proj_v8m"])
        ptabs.append(pt[pt.season == s])
        if not pl.empty:
            pltabs.append(pl[pl.season == s])
        folds.append(fold[fold["season"] == s])
    df = pd.concat(folds, ignore_index=True).dropna(subset=[f"proj_{m}" for m in MODELS])
    w1 = df[df.week == 1].copy()
    idx = big60_pool(w1, "proj_base").index
    for m in MODELS[1:]:
        idx = idx.union(big60_pool(w1, f"proj_{m}").index)
    big = w1.loc[idx]
    rest = df[df.week > 1]
    rest_big = rest.loc[big60_pool(rest, "proj_base").index.union(big60_pool(rest, "proj_v8m").index)]
    pt = pd.concat(ptabs, ignore_index=True)
    pl = pd.concat(pltabs, ignore_index=True) if pltabs else pd.DataFrame()

    L = ["# Experiment: Week 1 effect on the median (v11 / v11p), forward-chained OOS 2020–2023", "",
         "## Position-level Week 1 effect (fitted on Week 1s of seasons 2019..s−1; γ = % vs the v8m median)", "",
         "| season | position | n | raw γ | se | τ² | shrinkage B | shrunk γ |", "|---|---|---|---|---|---|---|---|"]
    L += [f"| {r.season} | {r.position} | {r.n} | {100 * r.raw:+.1f}% | {100 * r.se:.1f}% | {r.tau2:.4f} | {r.B:.2f} | {100 * r.gamma:+.1f}% |"
          for r in pt.sort_values(["season", "position"]).itertuples()]
    L += ["", "## Player-level deviations (v11p): how much each player's own Week 1 history is trusted", "",
          "| season | position | players | with ≥ 2 earlier openers | average B | max |deviation| |", "|---|---|---|---|---|---|"]
    if pl.empty:
        L.append("| – | – | – | – | – | – |")
    for (s, p), a in (pl.groupby(["season", "position"]) if not pl.empty else []):
        L.append(f"| {s} | {p} | {len(a)} | {(a.n >= 2).sum()} | {a.B.mean():.2f} | {100 * a.dev.abs().max():.1f}% |")
    L += ["", "## Results, Week 1 only (Big-60 = union of all four models' pools; clusters = games)", "",
          "| pool | A vs B | n | MAE A | MAE B | diff (A−B) | 95% CI | p(A not better) |", "|---|---|---|---|---|---|---|---|"]
    for name, d in {"big60 week 1": big, "all players week 1": w1}.items():
        for a, b in COMPARE:
            r = paired_bootstrap((d["actual"] - d[f"proj_{a}"]).abs(), (d["actual"] - d[f"proj_{b}"]).abs(), d["game_id"])
            L.append(f"| {name} | {a} vs {b} | {len(d)} | {mae(d['actual'], d[f'proj_{a}']):.3f} | {mae(d['actual'], d[f'proj_{b}']):.3f} | "
                     f"{r['diff']:+.3f} | [{r['ci_low']:+.3f}, {r['ci_high']:+.3f}] | {r['p_a_not_better']:.3f} |")
    L += ["", "## Diagnostics: is Week 1 different for v8m? (Big-60; descriptive)", "",
          "| position | Week 1 n | Week 1 median error (proj − actual) | Week 1 share scoring above median | "
          "weeks 2+ share above median | Week 1 floor–ceiling coverage | weeks 2+ coverage |", "|---|---|---|---|---|---|---|"]
    for p in POS + ["all"]:
        a = big if p == "all" else big[big.position == p]
        b = rest_big if p == "all" else rest_big[rest_big.position == p]
        ca, cb = coverage(a.actual, a.lo, a.hi), coverage(b.actual, b.lo, b.hi)
        L.append(f"| {p} | {len(a)} | {np.median(a.proj_v8m - a.actual):+.2f} | {(a.actual > a.proj_v8m).mean():.1%} | "
                 f"{(b.actual > b.proj_v8m).mean():.1%} | {ca['inside']:.1%} | {cb['inside']:.1%} |")
    L += ["", "## Big-60 Week 1 MAE by position (descriptive)", "", "| model | " + " | ".join(POS) + " |", "|---|" + "---|" * len(POS)]
    for m in MODELS:
        L.append(f"| {m} | " + " | ".join(f"{mae(big.loc[big.position == p, 'actual'], big.loc[big.position == p, f'proj_{m}']):.3f}"
                                         for p in POS) + " |")
    (PROJECT_ROOT / "reports" / "exp_week1.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
