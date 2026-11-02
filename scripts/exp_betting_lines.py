"""Experiment: betting lines for team volume (v4) vs current v2. Dev seasons only.

Pre-registered (DECISIONS.md, 2026-11-01):
  v4 = team context with team volume from history + implied points + spread
       (OLS fitted on earlier seasons only); everything else as v3.
  Same framework as the paper ablation: relevant-player tuning, forward-chaining OOS 2020–2023,
  Big-60 union pool, paired week-clustered bootstrap.
  Headline: v4 vs v2. Secondary: v4 vs v3 (value of lines given team structure), v4 vs baseline.

Placebo check (--placebo): betting lines are shuffled between team-games within each season,
keeping their distribution but destroying any link to the actual game. If v4's gain survives,
the pipeline leaks; if it vanishes, the information really comes from the lines.

Clean ablation (--ablation): adds v4reg = same regression on team history only (no lines).
v4 vs v4reg isolates the betting-market information.

Usage: uv run python scripts/exp_betting_lines.py [--placebo] [--ablation]
"""

import sys

import numpy as np
import pandas as pd

from fantasy_projection_engine import DEV_SEASONS, predict
from fantasy_projection_engine.baseline import add_projection, big60_pool, prepare_games
from fantasy_projection_engine.betting import add_lines, build_team_lines
from fantasy_projection_engine.data import PROJECT_ROOT, load_player_stats, load_players, load_schedules, load_snap_counts
from fantasy_projection_engine.metrics import mae, paired_bootstrap
from fantasy_projection_engine.opp_eff import COMPONENTS, add_components, project
from fantasy_projection_engine.player_games import build_player_games
from fantasy_projection_engine.team_context import add_team_totals, build_team_games
from fantasy_projection_engine.tuning import VOL_SHRINK_V2, relevant_mask, tune_baseline, tune_opp_eff

ABLATION = "--ablation" in sys.argv
if ABLATION:  # clean ablation (pre-registered): isolate the betting-market information
    MODELS = ["base", "v2", "v4reg", "v4"]
    VARIANTS = {"v2": dict(team=False), "v4reg": dict(team=True, team_reg=True), "v4": dict(team=True, lines=True)}
    COMPARE = [("v4", "v4reg"), ("v4reg", "v2"), ("v4", "v2"), ("v4", "base")]
else:
    MODELS = ["base", "v2", "v3", "v4"]
    VARIANTS = {"v2": dict(team=False), "v3": dict(team=True), "v4": dict(team=True, lines=True)}
    COMPARE = [("v4", "v2"), ("v4", "v3"), ("v4", "base"), ("v2", "base")]


def fmt(p):
    return " | ".join(
        f"{p[c].hl_vol}/{p[c].hl_eff}/{p[c].k}/{p[c].hl_long if p[c].m else '–'}/{p[c].m}/{p[c].hl_team if p[c].team else '–'}"
        for c in COMPONENTS)


def shuffle_lines(lines: pd.DataFrame, seed: int = 0) -> pd.DataFrame:
    """Placebo: permute (implied, margin) pairs across team-games within each season."""
    rng = np.random.default_rng(seed)
    out = lines.copy()
    for _, idx in out.groupby("season").groups.items():
        perm = rng.permutation(len(idx))
        out.loc[idx, ["implied", "margin"]] = out.loc[idx, ["implied", "margin"]].to_numpy()[perm]
    return out


def load_games(placebo: bool = False):
    return predict.load_games(shuffle_lines if placebo else None)


def main():
    placebo = "--placebo" in sys.argv
    g = load_games(placebo)
    rel = relevant_mask(g)
    cache, folds, settings = {}, [], []
    for s in DEV_SEASONS[1:]:
        train = [t for t in DEV_SEASONS if t < s]
        fold = add_projection(g, tune_baseline(g, train), "proj_base")
        for name, kw in VARIANTS.items():
            params, _ = tune_opp_eff(g, train, cache, VOL_SHRINK_V2, rel, **kw)
            fold[f"proj_{name}"] = project(g, params, cache)["proj"].to_numpy()
            settings.append(f"| {s} | {name} | {fmt(params)} |")
        folds.append(fold[fold["season"] == s])
    df = pd.concat(folds, ignore_index=True).dropna(subset=[f"proj_{m}" for m in MODELS])
    df["cluster"] = df["season"].astype(str) + "-" + df["week"].astype(str)
    idx = big60_pool(df, "proj_base").index
    for m in MODELS[1:]:
        idx = idx.union(big60_pool(df, f"proj_{m}").index)
    big = df.loc[idx]

    title = ("PLACEBO (lines shuffled within season)" if placebo
             else "CLEAN ABLATION: lines vs history-only regression" if ABLATION else "betting lines for team volume (v4)")
    L = [f"# Experiment: {title}, forward-chained OOS 2020–2023", "",
         "## Settings per fold (hl_vol/hl_eff/k/hl_long/m/hl_team)", "",
         "| season | model | rec | rush | pass |", "|---|---|---|---|---|", *settings, "",
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
    name = "exp_betting_lines" + ("_placebo" if placebo else "") + ("_ablation" if ABLATION else "")
    out = PROJECT_ROOT / "reports" / f"{name}.md"
    out.write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
