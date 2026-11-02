"""Experiment: does volume shrinkage (OE v2) beat OE v1 and the baseline? Dev seasons only.

Forward-chaining out-of-sample: to score season s (2020–2023), every model is tuned only
on dev seasons < s. Paired week-clustered bootstrap on identical player-games.

Usage: uv run python scripts/exp_vol_shrink.py
"""

import numpy as np
import pandas as pd

from fantasy_projection_engine import DEV_SEASONS
from fantasy_projection_engine.baseline import add_projection, big60_pool, prepare_games
from fantasy_projection_engine.data import PROJECT_ROOT, load_player_stats, load_players, load_snap_counts
from fantasy_projection_engine.metrics import mae, paired_bootstrap
from fantasy_projection_engine.opp_eff import COMPONENTS, add_components, project
from fantasy_projection_engine.player_games import build_player_games
from fantasy_projection_engine.tuning import VOL_SHRINK_V1, VOL_SHRINK_V2, tune_baseline, tune_opp_eff

KEY = ["player_id", "season", "week"]


def fmt(p):
    return " | ".join(f"{p[c].hl_vol}/{p[c].hl_eff}/{p[c].k}/{p[c].hl_long if p[c].m else '–'}/{p[c].m}" for c in COMPONENTS)


def main():
    g = add_components(prepare_games(build_player_games(load_player_stats(), load_snap_counts(), load_players())))
    cache, folds, settings = {}, [], []
    for s in DEV_SEASONS[1:]:
        train = [t for t in DEV_SEASONS if t < s]
        p1, _ = tune_opp_eff(g, train, cache, VOL_SHRINK_V1)
        p2, _ = tune_opp_eff(g, train, cache, VOL_SHRINK_V2)
        base = add_projection(g, tune_baseline(g, train), "proj_base")
        v1 = project(g, p1, cache)[KEY + ["proj"]].rename(columns={"proj": "proj_v1"})
        v2 = project(g, p2, cache).rename(columns={"proj": "proj_v2"})
        fold = v2.merge(v1, on=KEY).merge(base[KEY + ["proj_base"]], on=KEY)
        folds.append(fold[fold["season"] == s])
        settings.append(f"| {s} | v2 | {fmt(p2)} |")
    df = pd.concat(folds, ignore_index=True).dropna(subset=["proj_base", "proj_v1", "proj_v2"])
    df["cluster"] = df["season"].astype(str) + "-" + df["week"].astype(str)
    idx = big60_pool(df, "proj_base").index
    for c in ["proj_v1", "proj_v2"]:
        idx = idx.union(big60_pool(df, c).index)
    big = df.loc[idx]

    lines = ["# Experiment: volume shrinkage (OE v2), forward-chaining out-of-sample 2020–2023", "",
             "## v2 settings per fold (hl_vol/hl_eff/k/hl_long/m)", "",
             "| season | model | rec | rush | pass |", "|---|---|---|---|---|", *settings, "",
             "## Results (Big-60 = union of all three models' own pools)", "",
             "| pool | comparison | n | MAE A | MAE B | diff (A−B) | 95% CI | p(A not better) |",
             "|---|---|---|---|---|---|---|---|"]
    pools = {"big60": big, "all": df, **{f"big60 {p}": big[big["position"] == p] for p in ["QB", "RB", "WR", "TE"]}}
    for name, d in pools.items():
        for a, b in [("proj_v2", "proj_base"), ("proj_v2", "proj_v1")]:
            r = paired_bootstrap((d["actual"] - d[a]).abs(), (d["actual"] - d[b]).abs(), d["cluster"])
            lines.append(f"| {name} | {a[5:]} vs {b[5:]} | {len(d)} | {mae(d['actual'], d[a]):.3f} | {mae(d['actual'], d[b]):.3f} | "
                         f"{r['diff']:+.3f} | [{r['ci_low']:+.3f}, {r['ci_high']:+.3f}] | {r['p_a_not_better']:.3f} |")
    lines += ["", "## Bias in Big-60 pool (mean projection − actual)", "",
              "| base | v1 | v2 |", "|---|---|---|",
              f"| {np.mean(big['proj_base'] - big['actual']):+.2f} | {np.mean(big['proj_v1'] - big['actual']):+.2f} | "
              f"{np.mean(big['proj_v2'] - big['actual']):+.2f} |"]
    out = PROJECT_ROOT / "reports" / "exp_vol_shrink.md"
    out.write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
