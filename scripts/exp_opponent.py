"""Experiment: opponent strength by position (v14) vs v8m, with a shuffled-opponent placebo. Dev seasons only.

Pre-registered (DECISIONS.md, 2026-11-02):
  v14       median × (1 + δ), δ = schedule-adjusted defense-vs-position effect (half-life 8 defense-games),
            relative to the league ratio, EB-shrunk per position; hyperparameters from seasons 2020..s−1
  placebo   same, but each team's opponent replaced by a random other team that week
  Headline: v14 vs v8m, Big-60 union, all weeks, OOS 2021–23, week-clustered.
  Adopt if p < 0.05 AND v14 has lower MAE than the placebo.

Usage: uv run python scripts/exp_opponent.py
"""

import numpy as np
import pandas as pd

from fantasy_projection_engine import DEV_SEASONS
from fantasy_projection_engine.baseline import add_projection, big60_pool
from fantasy_projection_engine.calibration import median_calibration
from fantasy_projection_engine.data import PROJECT_ROOT
from fantasy_projection_engine.metrics import mae, paired_bootstrap
from fantasy_projection_engine.opp_eff import project
from fantasy_projection_engine.opponent import matchup_table, opponent_multiplier, opponents, placebo_opponents
from fantasy_projection_engine.tuning import VOL_SHRINK_V2, relevant_mask, tune_baseline, tune_opp_eff

from exp_betting_lines import load_games
from exp_eff_lines import with_eff_adj

MODELS = ["base", "v8m", "v14", "v14placebo"]
POS = ["QB", "RB", "WR", "TE"]
HEADLINE_FROM = 2021


def boot_row(name, d, a, b):
    r = paired_bootstrap((d["actual"] - d[f"proj_{a}"]).abs(), (d["actual"] - d[f"proj_{b}"]).abs(), d["cluster"])
    return (f"| {name} | {a} vs {b} | {len(d)} | {mae(d['actual'], d[f'proj_{a}']):.3f} | {mae(d['actual'], d[f'proj_{b}']):.3f} | "
            f"{r['diff']:+.3f} | [{r['ci_low']:+.3f}, {r['ci_high']:+.3f}] | {r['p_a_not_better']:.3f} |")


def stickiness(tab):
    """Per position: correlation between a defense's first-half (weeks 1–9) and second-half deviation, same season."""
    out = {}
    for p, a in tab.groupby("position"):
        a = a.assign(half=np.where(a.week <= 9, "h1", "h2"))
        R = a.groupby(["season", "half"])[["A", "M"]].transform("sum")
        a = a.assign(RA=R["A"], RM=R["M"])
        h = a.groupby(["defense", "season", "half"]).agg(A=("A", "sum"), M=("M", "sum"), RA=("RA", "first"), RM=("RM", "first"))
        h["dev"] = (h.A / h.M) / (h.RA / h.RM) - 1
        w = h["dev"].unstack("half").dropna()
        out[p] = (w["h1"].corr(w["h2"]), len(w))
    return out


def main():
    g = load_games()
    opp = opponents(g)
    fake = placebo_opponents(g, opp, seed=0)
    rel = relevant_mask(g)
    cache, folds, hps, effs = {}, [], [], []
    for s in DEV_SEASONS[1:]:
        train = [t for t in DEV_SEASONS if t < s]
        fold = add_projection(g, tune_baseline(g, train), "proj_base")
        v4, _ = tune_opp_eff(g, train, cache, VOL_SHRINK_V2, rel, team=True, lines=True)
        fold["raw"] = project(g, with_eff_adj(v4, "lines"), cache)["proj"].to_numpy()
        fold["proj_v8m"] = median_calibration(fold, "raw", rel, "lad_mult")[0]
        m14, hp, eff = opponent_multiplier(fold, "proj_v8m", rel, opp)
        mph, hpp, _ = opponent_multiplier(fold, "proj_v8m", rel, fake)
        fold["proj_v14"], fold["proj_v14placebo"] = fold["proj_v8m"] * m14, fold["proj_v8m"] * mph
        fold["delta"], fold["B"] = eff["delta"].to_numpy(), eff["B"].to_numpy()
        if not hp.empty:
            hps.append(hp[hp.season == s].merge(hpp[hpp.season == s][["position", "tau2"]].rename(columns={"tau2": "tau2_placebo"}),
                                                 on="position"))
        if s == DEV_SEASONS[-1]:
            stick = stickiness(matchup_table(fold, "proj_v8m", rel, opp))
            stick_fake = stickiness(matchup_table(fold, "proj_v8m", rel, fake))
        folds.append(fold[fold["season"] == s])
    df = pd.concat(folds, ignore_index=True).dropna(subset=[f"proj_{m}" for m in MODELS])
    df["cluster"] = df["season"].astype(str) + "-" + df["week"].astype(str)
    idx = big60_pool(df, "proj_base").index
    for m in MODELS[1:]:
        idx = idx.union(big60_pool(df, f"proj_{m}").index)
    big = df.loc[idx]
    h = big[big.season >= HEADLINE_FROM]
    hp = pd.concat(hps, ignore_index=True)

    L = ["# Experiment: opponent strength by position (v14 + shuffled-opponent placebo), forward-chained OOS 2020–2023", "",
         "Defense effect = how much the players it faced beat their own v8m median, relative to the league ratio, "
         "decayed (half-life 8 defense-games), EB-shrunk per position. Hyperparameters from seasons 2020..s−1.", "",
         "## Hyperparameters per fold", "",
         "| season | position | league ratio R (mean/median) | σ² (per expected pt) | τ² | true spread of defenses (sd = √τ²) | placebo τ² | defense-seasons |",
         "|---|---|---|---|---|---|---|---|"]
    L += [f"| {r.season} | {r.position} | {r.R:.3f} | {r.sigma2:.3f} | {r.tau2:.4f} | {100 * np.sqrt(r.tau2):.1f}% | {r.tau2_placebo:.4f} | {r.defense_seasons} |"
          for r in hp.sort_values(["season", "position"]).itertuples()]
    L += ["", f"## Shrunk effects δ applied (all rows, {HEADLINE_FROM}–23)", "",
          "| position | average shrinkage B | δ 10th pct | δ median | δ 90th pct | max |δ| |", "|---|---|---|---|---|---|"]
    a_ = df[df.season >= HEADLINE_FROM]
    for p in POS:
        a = a_[a_.position == p]
        L.append(f"| {p} | {a.B.mean():.2f} | {100 * a.delta.quantile(.1):+.1f}% | {100 * a.delta.median():+.1f}% | "
                 f"{100 * a.delta.quantile(.9):+.1f}% | {100 * a.delta.abs().max():.1f}% |")
    L += ["", f"## Results (Big-60 = union of all four models' pools; all weeks; week-clustered; headline {HEADLINE_FROM}–23)", "",
          "| pool | A vs B | n | MAE A | MAE B | diff (A−B) | 95% CI | p(A not better) |", "|---|---|---|---|---|---|---|---|",
          boot_row("**big60 (headline)**", h, "v14", "v8m"),
          boot_row("big60", h, "v14placebo", "v8m"),
          boot_row("big60", h, "v14", "v14placebo"),
          boot_row("all players", df[df.season >= HEADLINE_FROM], "v14", "v8m"),
          boot_row("big60 2020–23 (descriptive)", big, "v14", "v8m"),
          boot_row("big60", h, "v8m", "base")]
    for p in POS:
        L.append(boot_row(f"big60 {p} (descriptive)", h[h.position == p], "v14", "v8m"))
    L += ["", "## Stickiness: does a defense's first-half deviation predict its second half? (2020–23, descriptive)", "",
          "| position | correlation (real opponents) | correlation (placebo opponents) | defense-seasons |", "|---|---|---|---|"]
    for p in POS:
        L.append(f"| {p} | {stick[p][0]:+.2f} | {stick_fake[p][0]:+.2f} | {stick[p][1]} |")
    (PROJECT_ROOT / "reports" / "exp_opponent.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
