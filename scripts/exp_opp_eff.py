"""Experiment: opportunity × efficiency (OE) vs the trailing-average baseline. Dev seasons only.

OUT-OF-SAMPLE via forward-chaining: to score season s (2020–2023), BOTH models are
tuned only on dev seasons before s (2019..s−1). No season is scored by settings that saw it.

Same games, paired week-clustered bootstrap. Big-60 pool = union of each model's own
weekly top 10/20/20/10 by its own projection.

Usage: uv run python scripts/exp_opp_eff.py
"""

import numpy as np
import pandas as pd

from fantasy_projection_engine import DEV_SEASONS
from fantasy_projection_engine.baseline import add_projection, big60_pool, prepare_games
from fantasy_projection_engine.data import PROJECT_ROOT, load_player_stats, load_players, load_snap_counts
from fantasy_projection_engine.metrics import mae, paired_bootstrap
from fantasy_projection_engine.opp_eff import add_components, project
from fantasy_projection_engine.player_games import build_player_games
from fantasy_projection_engine.tuning import tune_baseline, tune_opp_eff

KEY = ["player_id", "season", "week"]


def main():
    g = add_components(prepare_games(build_player_games(load_player_stats(), load_snap_counts(), load_players())))
    cache, folds, settings = {}, [], []
    for s in DEV_SEASONS[1:]:
        train = [t for t in DEV_SEASONS if t < s]
        params, _ = tune_opp_eff(g, train, cache)
        method = tune_baseline(g, train)
        oe = project(g, params, cache).rename(columns={"proj": "proj_oe"})
        base = add_projection(g, method, "proj_base")
        fold = oe.merge(base[KEY + ["proj_base"]], on=KEY)
        folds.append(fold[fold["season"] == s])
        settings.append(f"| {s} | {train[0]}–{train[-1]} | {method} | "
                        + " | ".join(f"{params[c].hl_vol}/{params[c].hl_eff}/{params[c].k}" for c in ["rec", "rush", "pass"]) + " |")
    df = pd.concat(folds, ignore_index=True)
    df = df.dropna(subset=["proj_oe", "proj_base"])
    df["cluster"] = df["season"].astype(str) + "-" + df["week"].astype(str)
    big = df.loc[big60_pool(df, "proj_oe").index.union(big60_pool(df, "proj_base").index)]

    lines = ["# Experiment: opportunity × efficiency vs baseline, forward-chaining out-of-sample", "",
             "## Settings chosen in each fold (OE given as hl_vol/hl_eff/k)", "",
             "| scored season | tuned on | baseline method | rec | rush | pass |", "|---|---|---|---|---|---|",
             *settings, "", "## Out-of-sample results, seasons 2020–2023 pooled", "",
             "| pool | n | MAE base | MAE OE | diff (OE−base) | 95% CI | p(OE not better) | bias base | bias OE |",
             "|---|---|---|---|---|---|---|---|---|"]
    pools = {"big60 (union)": big, "all": df}
    for pos in ["QB", "RB", "WR", "TE"]:
        pools[f"big60 {pos}"] = big[big["position"] == pos]
    for name, d in pools.items():
        b = paired_bootstrap((d["actual"] - d["proj_oe"]).abs(), (d["actual"] - d["proj_base"]).abs(), d["cluster"])
        lines.append(
            f"| {name} | {len(d)} | {mae(d['actual'], d['proj_base']):.3f} | {mae(d['actual'], d['proj_oe']):.3f} | "
            f"{b['diff']:+.3f} | [{b['ci_low']:+.3f}, {b['ci_high']:+.3f}] | {b['p_a_not_better']:.3f} | "
            f"{np.mean(d['proj_base'] - d['actual']):+.2f} | {np.mean(d['proj_oe'] - d['actual']):+.2f} |"
        )

    # How much shrinkage happens, for players in the Big-60 pool?
    lines += ["", "## Shrinkage share in the Big-60 pool (k / (opportunities + k); 1 = all league average)", "",
              "| component | position | median | 10th pct | 90th pct |", "|---|---|---|---|---|"]
    for c, pos_list in {"rec": ["RB", "WR", "TE"], "rush": ["QB", "RB"], "pass": ["QB"]}.items():
        for pos in pos_list:
            s = big.loc[big["position"] == pos, f"shrink_{c}"]
            lines.append(f"| {c} | {pos} | {s.median():.2f} | {s.quantile(.1):.2f} | {s.quantile(.9):.2f} |")

    out = PROJECT_ROOT / "reports" / "exp_opp_eff.md"
    out.write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
