"""Experiment: vacated opportunity from injured teammates (v7) vs v5. Dev seasons only.

Pre-registered (DECISIONS.md, 2026-11-02):
  v7 = v5 with rec/rush share × (1 + λ_same·V_same + λ_other·V_other), V = vacated share of
       teammates designated Out/Doubtful before kickoff; λ fitted walk-forward (seasons < s).
  v7-placebo: each team-week's absences moved to a random other team playing that week.
  Headline: v7 vs v5. Adopt only if p < 0.05 and the placebo shows no significant gain.

Usage: uv run python scripts/exp_vacated.py
"""

from dataclasses import replace

import numpy as np
import pandas as pd

from fantasy_projection_engine import DEV_SEASONS
from fantasy_projection_engine.baseline import add_projection, big60_pool
from fantasy_projection_engine.data import PROJECT_ROOT, load_injuries, load_schedules
from fantasy_projection_engine.injuries import build_absences, link_absences
from fantasy_projection_engine.metrics import mae, paired_bootstrap
from fantasy_projection_engine.opp_eff import project
from fantasy_projection_engine.tuning import VOL_SHRINK_V2, relevant_mask, tune_baseline, tune_opp_eff

from exp_betting_lines import fmt, load_games
from exp_eff_lines import with_eff_adj

MODELS = ["base", "v5", "v7placebo", "v7"]
COMPARE = [("v7", "v5"), ("v7placebo", "v5"), ("v7", "v7placebo"), ("v7", "base")]


def placebo_links(links: pd.DataFrame, g: pd.DataFrame, seed: int = 0) -> pd.DataFrame:
    """Move each team-week's absences to a random other team playing that same week (a derangement)."""
    rng = np.random.default_rng(seed)
    teams = g[["season", "week", "team"]].drop_duplicates()
    maps = []
    for (s, w), t in teams.groupby(["season", "week"]):
        names = t["team"].to_numpy()
        while True:
            perm = rng.permutation(len(names))
            if len(names) < 2 or (perm != np.arange(len(names))).all():
                break
        maps.append(pd.DataFrame({"season": s, "week": w, "team": names, "new_team": names[perm]}))
    m = links.merge(pd.concat(maps), on=["season", "week", "team"], how="left")
    return m.assign(team=m["new_team"].fillna(m["team"])).drop(columns="new_team")


def with_vacated(params):
    return {c: (replace(p, vacated=True) if c in ("rec", "rush") else p) for c, p in params.items()}


def main():
    g = load_games()
    rel = relevant_mask(g)
    absences = build_absences(load_injuries(), load_schedules())
    cache, folds, settings, coefs = {}, [], [], []
    cache[("links", "real")] = link_absences(g, absences)
    cache[("links", "placebo")] = placebo_links(cache[("links", "real")], g)
    n_abs = absences[absences.season.isin(DEV_SEASONS)]
    n_link = cache[("links", "real")].query("season in @DEV_SEASONS")
    for s in DEV_SEASONS[1:]:
        train = [t for t in DEV_SEASONS if t < s]
        fold = add_projection(g, tune_baseline(g, train), "proj_base")
        v4, _ = tune_opp_eff(g, train, cache, VOL_SHRINK_V2, rel, team=True, lines=True)
        v5 = with_eff_adj(v4, "lines")
        v7 = with_vacated(v5)
        settings.append(f"| {s} | {fmt(v4)} |")
        fold["proj_v5"] = project(g, v5, cache)["proj"].to_numpy()
        for name, tag in [("v7", "real"), ("v7placebo", "placebo")]:
            fold[f"proj_{name}"] = project(g, v7, cache, absence_tag=tag)["proj"].to_numpy()
            for c in ("rec", "rush"):
                lam = {ss: (a, b) for ss, a, b in cache[("vac_coefs", c, tag, v7[c])]}[s]
                coefs.append(f"| {s} | {name} | {c} | {lam[0]:+.2f} | {lam[1]:+.2f} |")
        fold["affected"] = (cache[("vac_V", "rec", "real", v7["rec"])] + cache[("vac_V", "rush", "real", v7["rush"])]) > 0
        folds.append(fold[fold["season"] == s])
    df = pd.concat(folds, ignore_index=True).dropna(subset=[f"proj_{m}" for m in MODELS])
    df["cluster"] = df["season"].astype(str) + "-" + df["week"].astype(str)
    idx = big60_pool(df, "proj_base").index
    for m in MODELS[1:]:
        idx = idx.union(big60_pool(df, f"proj_{m}").index)
    big = df.loc[idx]

    L = ["# Experiment: vacated opportunity from injured teammates (v7), forward-chained OOS 2020–2023", "",
         f"Absences (Out/Doubtful, skill positions, dev seasons): {len(n_abs):,}; linked to a prior game for "
         f"the same team: {len(n_link):,}. Big-60 player-games with an absent teammate (V > 0): "
         f"{big['affected'].sum():,} of {len(big):,} ({100 * big['affected'].mean():.0f}%).", "",
         "## v5 settings per fold (hl_vol/hl_eff/k/hl_long/m/hl_team)", "",
         "| season | rec | rush | pass |", "|---|---|---|---|", *settings, "",
         "## Fitted λ (from seasons < s): % growth in share per unit of vacated share", "",
         "| season | model | component | λ same position | λ other positions |", "|---|---|---|---|---|", *coefs, "",
         "## Results (Big-60 = union of all four models' pools)", "",
         "| pool | A vs B | n | MAE A | MAE B | diff (A−B) | 95% CI | p(A not better) |", "|---|---|---|---|---|---|---|---|"]
    pools = {"big60": big, "all": df, "big60, absent teammate (descriptive)": big[big["affected"]]}
    for name, d in pools.items():
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
    (PROJECT_ROOT / "reports" / "exp_vacated.md").write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
