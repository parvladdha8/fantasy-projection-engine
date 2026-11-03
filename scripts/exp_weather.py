"""Experiment: bad-weather effect on the median projection (v13 + two placebos). Dev seasons only.

Pre-registered (DECISIONS.md, 2026-11-02):
  bad weather  = roof outdoors/open AND (wind ≥ 15 mph OR temp ≤ 32°F); missing weather → not flagged
  v13          bad-weather median = v8m × (1 + γ_pos), LAD on earlier bad-weather games (seasons ≥ 2020), EB-shrunk
  placebo_any  label on random games (same count per week)
  placebo_out  label on random OUTDOOR games (same count per week)
  Headline: v13 vs v8m, Big-60 bad-weather rows, OOS 2021–23, week-clustered.
  Adopt if p < 0.05 AND v13 beats both placebos on their own labelled rows.

Usage: uv run python scripts/exp_weather.py
"""

import numpy as np
import pandas as pd

from fantasy_projection_engine import DEV_SEASONS
from fantasy_projection_engine.baseline import add_projection, big60_pool
from fantasy_projection_engine.calibration import median_calibration, quantile_band, shrunk_volatility
from fantasy_projection_engine.data import PROJECT_ROOT, load_schedules
from fantasy_projection_engine.metrics import coverage, mae, paired_bootstrap
from fantasy_projection_engine.opp_eff import project
from fantasy_projection_engine.situational import placebo_flags, situation_multiplier, weather_flags
from fantasy_projection_engine.tuning import VOL_SHRINK_V2, relevant_mask, tune_baseline, tune_opp_eff

from exp_betting_lines import load_games
from exp_eff_lines import with_eff_adj

MODELS = ["base", "v8m", "v13", "v13any", "v13out"]
POS = ["QB", "RB", "WR", "TE"]
HEADLINE_FROM = 2021


def boot_row(name, d, a, b):
    r = paired_bootstrap((d["actual"] - d[f"proj_{a}"]).abs(), (d["actual"] - d[f"proj_{b}"]).abs(), d["cluster"])
    return (f"| {name} | {a} vs {b} | {len(d)} | {mae(d['actual'], d[f'proj_{a}']):.3f} | {mae(d['actual'], d[f'proj_{b}']):.3f} | "
            f"{r['diff']:+.3f} | [{r['ci_low']:+.3f}, {r['ci_high']:+.3f}] | {r['p_a_not_better']:.3f} |")


def main():
    g = load_games()
    wf = weather_flags(load_schedules())
    g = g.merge(wf, on="game_id", how="left", validate="many_to_one")
    assert g["bad_weather"].notna().all()
    g["z"] = shrunk_volatility(g).to_numpy()
    bad = g["bad_weather"].to_numpy(bool)
    any_fake = placebo_flags(g, bad, seed=0)
    out_fake = placebo_flags(g, bad, seed=0, eligible=g["outdoor"].to_numpy(bool))
    rel = relevant_mask(g)
    every = np.ones(len(g), bool)
    cache, folds, tabs = {}, [], {"v13": [], "v13any": [], "v13out": []}
    for s in DEV_SEASONS[1:]:
        train = [t for t in DEV_SEASONS if t < s]
        fold = add_projection(g, tune_baseline(g, train), "proj_base")
        v4, _ = tune_opp_eff(g, train, cache, VOL_SHRINK_V2, rel, team=True, lines=True)
        fold["raw"] = project(g, with_eff_adj(v4, "lines"), cache)["proj"].to_numpy()
        fold["proj_v8m"] = median_calibration(fold, "raw", rel, "lad_mult")[0]
        for m, f in [("v13", bad), ("v13any", any_fake), ("v13out", out_fake)]:
            mult, t, _ = situation_multiplier(fold, "proj_v8m", rel, f)
            fold[f"proj_{m}"] = fold["proj_v8m"] * mult
            if not t.empty:
                tabs[m].append(t[t.season == s])
        for k, tau in [("lo", 0.1), ("hi", 0.9)]:
            fold[k] = quantile_band(fold, "raw", "z", every, tau)[0]
        fold["lo"], fold["hi"] = np.fmin(fold["lo"], fold["proj_v8m"]), np.fmax(fold["hi"], fold["proj_v8m"])
        fold["any_fake"], fold["out_fake"] = any_fake, out_fake
        folds.append(fold[fold["season"] == s])
    df = pd.concat(folds, ignore_index=True).dropna(subset=[f"proj_{m}" for m in MODELS])
    df["cluster"] = df["season"].astype(str) + "-" + df["week"].astype(str)
    idx = big60_pool(df, "proj_base").index
    for m in MODELS[1:]:
        idx = idx.union(big60_pool(df, f"proj_{m}").index)
    big = df.loc[idx]
    h = big[big.season >= HEADLINE_FROM]
    hb, hany, hout = h[h.bad_weather], h[h.any_fake], h[h.out_fake]
    tab = {m: pd.concat(v, ignore_index=True) for m, v in tabs.items()}

    gm = wf.merge(load_schedules()[["game_id", "season"]], on="game_id")
    gm = gm[gm.season.between(2019, 2023)]
    L = ["# Experiment: bad-weather effect on the median (v13 + two placebos), forward-chained OOS 2020–2023", "",
         "Bad weather = outdoor/open roof AND (wind ≥ 15 mph OR temp ≤ 32°F). Missing weather → not flagged.", "",
         "## Weather data by season (regular season)", "",
         "| season | games | outdoor/open | outdoor with missing weather | bad weather | wind only | cold only | both |",
         "|---|---|---|---|---|---|---|---|"]
    for s, a in gm.groupby("season"):
        L.append(f"| {s} | {len(a)} | {a.outdoor.sum()} | {(a.outdoor & ~a.weather_known).sum()} | {a.bad_weather.sum()} | "
                 f"{(a.cause == 'wind only').sum()} | {(a.cause == 'cold only').sum()} | {(a.cause == 'wind + cold').sum()} |")
    L += ["", "## Position-level bad-weather effect (fitted on bad-weather games of seasons 2020..s−1; γ = % vs v8m median)", "",
          "| season | position | n | raw γ | se | shrinkage B | shrunk γ | placebo (any game) γ | placebo (outdoor) γ |",
          "|---|---|---|---|---|---|---|---|---|"]
    pa = tab["v13any"].set_index(["season", "position"])["gamma"]
    po = tab["v13out"].set_index(["season", "position"])["gamma"]
    L += [f"| {r.season} | {r.position} | {r.n} | {100 * r.raw:+.1f}% | {100 * r.se:.1f}% | {r.B:.2f} | {100 * r.gamma:+.1f}% | "
          f"{100 * pa.get((r.season, r.position), np.nan):+.1f}% | {100 * po.get((r.season, r.position), np.nan):+.1f}% |"
          for r in tab["v13"].sort_values(["season", "position"]).itertuples()]
    L += ["", f"## Results (Big-60 = union of all five models' pools; week-clustered; headline seasons {HEADLINE_FROM}–2023)", "",
          "| pool | A vs B | n | MAE A | MAE B | diff (A−B) | 95% CI | p(A not better) |", "|---|---|---|---|---|---|---|---|",
          boot_row("**big60 bad weather (headline)**", hb, "v13", "v8m"),
          boot_row("big60 placebo-labelled games (any game)", hany, "v13any", "v8m"),
          boot_row("big60 placebo-labelled games (outdoor)", hout, "v13out", "v8m"),
          boot_row("all players bad weather", df[(df.season >= HEADLINE_FROM) & df.bad_weather], "v13", "v8m"),
          boot_row("big60 full season", h, "v13", "v8m"),
          boot_row("big60 full season", h, "v13", "v13any"),
          boot_row("big60 full season", h, "v13", "v13out"),
          boot_row("big60 bad weather, 2020–23 (descriptive)", big[big.bad_weather], "v13", "v8m")]
    L += ["", "## Diagnostics: is bad weather different for v8m? (Big-60, OOS 2020–23; descriptive)", "",
          "| group | n | median error (proj − actual) | share above median | floor–ceiling coverage |", "|---|---|---|---|---|"]
    bb = big[big.bad_weather]
    groups = [(c, big[big.cause == c]) for c in ["dome/closed", "outdoor, fine"]] + \
             [(f"bad weather, {p}", bb[bb.position == p]) for p in POS] + [("bad weather, all", bb)] + \
             [(f"cause: {c}", big[big.cause == c]) for c in ["wind only", "cold only", "wind + cold"]] + \
             [("outdoor, weather missing", big[big.outdoor & ~big.weather_known])]
    for name, a in groups:
        if len(a):
            L.append(f"| {name} | {len(a)} | {np.median(a.proj_v8m - a.actual):+.2f} | {(a.actual > a.proj_v8m).mean():.1%} | "
                     f"{coverage(a.actual, a.lo, a.hi)['inside']:.1%} |")
    L += ["", f"## Big-60 bad-weather MAE by position ({HEADLINE_FROM}–23; descriptive)", "",
          "| model | " + " | ".join(POS) + " |", "|---|" + "---|" * len(POS)]
    for m in MODELS:
        L.append(f"| {m} | " + " | ".join(f"{mae(hb.loc[hb.position == p, 'actual'], hb.loc[hb.position == p, f'proj_{m}']):.3f}"
                                         for p in POS) + " |")
    (PROJECT_ROOT / "reports" / "exp_weather.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
