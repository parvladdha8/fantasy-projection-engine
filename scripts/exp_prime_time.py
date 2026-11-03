"""Experiment: prime-time effect on the median projection (v12, v12p, placebo). Dev seasons only.

Pre-registered (DECISIONS.md, 2026-11-02):
  v12          prime-time median = v8m × (1 + γ_pos), LAD on earlier prime-time games, EB-shrunk toward 0
  v12p         v12 + player "prime-time split", partially pooled toward the position effect
  v12placebo   v12 with the label given to random games (same count per week)
  Headline: v12 vs v8m on Big-60 prime-time rows (week-clustered); adopt if p < 0.05 AND v12 beats the placebo.

Usage: uv run python scripts/exp_prime_time.py
"""

import numpy as np
import pandas as pd

from fantasy_projection_engine import DEV_SEASONS
from fantasy_projection_engine.baseline import add_projection, big60_pool
from fantasy_projection_engine.calibration import median_calibration, quantile_band, shrunk_volatility
from fantasy_projection_engine.data import PROJECT_ROOT, load_schedules
from fantasy_projection_engine.metrics import coverage, mae, paired_bootstrap
from fantasy_projection_engine.opp_eff import project
from fantasy_projection_engine.situational import placebo_flags, prime_time_flags, situation_multiplier
from fantasy_projection_engine.tuning import VOL_SHRINK_V2, relevant_mask, tune_baseline, tune_opp_eff

from exp_betting_lines import load_games
from exp_eff_lines import with_eff_adj

MODELS = ["base", "v8m", "v12", "v12p", "v12placebo"]
POS = ["QB", "RB", "WR", "TE"]


def boot_row(name, d, a, b):
    r = paired_bootstrap((d["actual"] - d[f"proj_{a}"]).abs(), (d["actual"] - d[f"proj_{b}"]).abs(), d["cluster"])
    return (f"| {name} | {a} vs {b} | {len(d)} | {mae(d['actual'], d[f'proj_{a}']):.3f} | {mae(d['actual'], d[f'proj_{b}']):.3f} | "
            f"{r['diff']:+.3f} | [{r['ci_low']:+.3f}, {r['ci_high']:+.3f}] | {r['p_a_not_better']:.3f} |")


def main():
    g = load_games()
    g = g.merge(prime_time_flags(load_schedules()), on="game_id", how="left", validate="many_to_one")
    assert g["prime_time"].notna().all()
    g["z"] = shrunk_volatility(g).to_numpy()
    pt = g["prime_time"].to_numpy(bool)
    fake = placebo_flags(g, pt, seed=0)
    rel = relevant_mask(g)
    every = np.ones(len(g), bool)
    cache, folds, ptabs, pltabs, phtabs = {}, [], [], [], []
    for s in DEV_SEASONS[1:]:
        train = [t for t in DEV_SEASONS if t < s]
        fold = add_projection(g, tune_baseline(g, train), "proj_base")
        v4, _ = tune_opp_eff(g, train, cache, VOL_SHRINK_V2, rel, team=True, lines=True)
        fold["raw"] = project(g, with_eff_adj(v4, "lines"), cache)["proj"].to_numpy()
        fold["proj_v8m"] = median_calibration(fold, "raw", rel, "lad_mult")[0]
        m12, t12, _ = situation_multiplier(fold, "proj_v8m", rel, pt, first_season=2019)
        m12p, _, pl = situation_multiplier(fold, "proj_v8m", rel, pt, player_level=True, first_season=2019)
        mph, tph, _ = situation_multiplier(fold, "proj_v8m", rel, fake, first_season=2019)
        fold["proj_v12"], fold["proj_v12p"], fold["proj_v12placebo"] = (fold["proj_v8m"] * m for m in (m12, m12p, mph))
        for k, tau in [("lo", 0.1), ("hi", 0.9)]:
            fold[k] = quantile_band(fold, "raw", "z", every, tau)[0]
        fold["lo"], fold["hi"] = np.fmin(fold["lo"], fold["proj_v8m"]), np.fmax(fold["hi"], fold["proj_v8m"])
        fold["fake"] = fake
        ptabs.append(t12[t12.season == s]), phtabs.append(tph[tph.season == s])
        if not pl.empty:
            pltabs.append(pl[pl.season == s])
        folds.append(fold[fold["season"] == s])
    df = pd.concat(folds, ignore_index=True).dropna(subset=[f"proj_{m}" for m in MODELS])
    df["cluster"] = df["season"].astype(str) + "-" + df["week"].astype(str)
    idx = big60_pool(df, "proj_base").index
    for m in MODELS[1:]:
        idx = idx.union(big60_pool(df, f"proj_{m}").index)
    big = df.loc[idx]
    bpt, bfake, apt = big[big.prime_time], big[big.fake], df[df.prime_time]
    t12, tph = pd.concat(ptabs, ignore_index=True), pd.concat(phtabs, ignore_index=True)
    pl = pd.concat(pltabs, ignore_index=True) if pltabs else pd.DataFrame()

    L = ["# Experiment: prime-time effect on the median (v12 / v12p / placebo), forward-chained OOS 2020–2023", "",
         f"Prime-time games (kickoff ≥ 19:00 ET) in 2020–23: {df.loc[df.prime_time, 'game_id'].nunique()} of "
         f"{df['game_id'].nunique()}. Big-60 prime-time player-games: {len(bpt)} of {len(big)}.", "",
         "## Position-level prime-time effect (fitted on prime-time games of seasons 2019..s−1; γ = % vs v8m median)", "",
         "| season | position | n | raw γ | se | shrinkage B | shrunk γ | placebo shrunk γ |", "|---|---|---|---|---|---|---|---|"]
    ph = tph.set_index(["season", "position"])["gamma"]
    L += [f"| {r.season} | {r.position} | {r.n} | {100 * r.raw:+.1f}% | {100 * r.se:.1f}% | {r.B:.2f} | {100 * r.gamma:+.1f}% | "
          f"{100 * ph.get((r.season, r.position), np.nan):+.1f}% |" for r in t12.sort_values(["season", "position"]).itertuples()]
    L += ["", "## Player-level prime-time splits (v12p): how much each player's own prime-time history is trusted", "",
          "| season | position | players | with ≥ 2 earlier prime-time games | average B | max |deviation| |", "|---|---|---|---|---|---|"]
    for (s, p), a in (pl.groupby(["season", "position"]) if not pl.empty else []):
        L.append(f"| {s} | {p} | {len(a)} | {(a.n >= 2).sum()} | {a.B.mean():.2f} | {100 * a.dev.abs().max():.1f}% |")
    L += ["", "## Results (Big-60 = union of all five models' pools; week-clustered)", "",
          "| pool | A vs B | n | MAE A | MAE B | diff (A−B) | 95% CI | p(A not better) |", "|---|---|---|---|---|---|---|---|",
          boot_row("**big60 prime time (headline)**", bpt, "v12", "v8m"),
          boot_row("big60 placebo-labelled games", bfake, "v12placebo", "v8m"),
          boot_row("big60 prime time", bpt, "v12p", "v12"),
          boot_row("big60 prime time", bpt, "v12p", "v8m"),
          boot_row("all players prime time", apt, "v12", "v8m"),
          boot_row("big60 full season", big, "v12", "v8m"),
          boot_row("big60 full season", big, "v12", "v12placebo"),
          boot_row("big60 full season", big, "v8m", "base")]
    L += ["", "## Diagnostics: is prime time different for v8m? (Big-60; descriptive)", "",
          "| group | n | median error (proj − actual) | share above median | floor–ceiling coverage |", "|---|---|---|---|---|"]
    groups = [("not prime time", big[~big.prime_time])] + [(f"prime time, {p}", bpt[bpt.position == p]) for p in POS] + \
             [("prime time, all", bpt)] + [(f"slot: {sl}", bpt[bpt.slot == sl]) for sl in sorted(bpt.slot.unique())]
    for name, a in groups:
        L.append(f"| {name} | {len(a)} | {np.median(a.proj_v8m - a.actual):+.2f} | {(a.actual > a.proj_v8m).mean():.1%} | "
                 f"{coverage(a.actual, a.lo, a.hi)['inside']:.1%} |")
    L += ["", "## Big-60 prime-time MAE by position (descriptive)", "", "| model | " + " | ".join(POS) + " |", "|---|" + "---|" * len(POS)]
    for m in MODELS:
        L.append(f"| {m} | " + " | ".join(f"{mae(bpt.loc[bpt.position == p, 'actual'], bpt.loc[bpt.position == p, f'proj_{m}']):.3f}"
                                         for p in POS) + " |")
    (PROJECT_ROOT / "reports" / "exp_prime_time.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
