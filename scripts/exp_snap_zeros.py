"""Experiment: does adding snap-count zero games improve the baseline?

Both versions are scored on the SAME complete set of player-games (stats rows
plus snap-only zero games), development seasons only.

  old = EWMA that skips zero games (Phase 1 behaviour)
  new = EWMA that includes them

Pools:
  all   = every player-game where both versions have a projection
  big60 = union of each version's own weekly top 10/20/20/10 (by its own projection),
          so neither version gets to pick a pool that flatters it.

Usage: uv run python scripts/exp_snap_zeros.py
"""

import numpy as np
import pandas as pd

from fantasy_projection_engine import DEV_SEASONS
from fantasy_projection_engine.baseline import METHODS, add_projection, big60_pool, prepare_games, score
from fantasy_projection_engine.data import PROJECT_ROOT, load_player_stats, load_players, load_snap_counts
from fantasy_projection_engine.metrics import mae, paired_bootstrap
from fantasy_projection_engine.player_games import build_player_games

METHOD = "ewma_hl8"
KEY = ["player_id", "season", "week"]


def main():
    pg = build_player_games(load_player_stats(), load_snap_counts(), load_players())
    old = add_projection(prepare_games(pg, include_snap_zeros=False), METHOD, "proj_old")
    new = add_projection(prepare_games(pg, include_snap_zeros=True), METHOD, "proj_new")
    df = old.merge(new[KEY + ["proj_new"]], on=KEY)
    df = df[df["season"].isin(DEV_SEASONS)].dropna(subset=["proj_old", "proj_new"])
    df["cluster"] = df["season"].astype(str) + "-" + df["week"].astype(str)

    in_old = big60_pool(df, "proj_old").index
    in_new = big60_pool(df, "proj_new").index
    pools = {"big60 (union)": df.loc[in_old.union(in_new)], "all": df}

    lines = [f"# Experiment: snap-count zero games ({METHOD}, dev {DEV_SEASONS[0]}–{DEV_SEASONS[-1]})", ""]
    lines.append(f"Zero games added in dev seasons: {(df['source'] == 'snaps_only').sum()} of {len(df)} scored player-games.\n")
    lines.append("| pool | n | MAE old | MAE new | diff (new−old) | 95% CI | p(new not better) |")
    lines.append("|---|---|---|---|---|---|---|")
    for name, d in pools.items():
        ea, eb = (d["actual"] - d["proj_new"]).abs(), (d["actual"] - d["proj_old"]).abs()
        b = paired_bootstrap(ea, eb, d["cluster"])
        lines.append(
            f"| {name} | {len(d)} | {mae(d['actual'], d['proj_old']):.3f} | {mae(d['actual'], d['proj_new']):.3f} | "
            f"{b['diff']:+.3f} | [{b['ci_low']:+.3f}, {b['ci_high']:+.3f}] | {b['p_a_not_better']:.3f} |"
        )

    # Bias check: average (projection − actual). Positive = projecting too high.
    lines += ["", "## Bias (mean projection − actual; + = too high)", "", "| pool | old | new |", "|---|---|---|"]
    for name, d in pools.items():
        lines.append(f"| {name} | {np.mean(d['proj_old'] - d['actual']):+.3f} | {np.mean(d['proj_new'] - d['actual']):+.3f} |")

    # Does the half-life choice still hold on the complete data?
    lines += ["", "## Half-life re-check on complete data (each method's own big60 pool)", "", "| method | MAE |", "|---|---|"]
    games = prepare_games(pg, include_snap_zeros=True)
    res = []
    for m in METHODS:
        g = add_projection(games, m)
        res.append((m, score(big60_pool(g[g["season"].isin(DEV_SEASONS)]))["mae"]))
    for m, v in sorted(res, key=lambda t: t[1]):
        lines.append(f"| {m} | {v:.3f} |")

    out = PROJECT_ROOT / "reports" / "exp_snap_zeros.md"
    out.write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
