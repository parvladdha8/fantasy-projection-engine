"""Tune opportunity × efficiency settings on ALL development seasons (2019–2023).

Reports the final settings and how sensitive error is to the shrinkage strength k.
(Out-of-sample evaluation lives in exp_opp_eff.py, which re-tunes inside each fold.)

Usage: uv run python scripts/tune_opp_eff.py
"""

import json
from dataclasses import asdict

from fantasy_projection_engine import DEV_SEASONS
from fantasy_projection_engine.baseline import prepare_games
from fantasy_projection_engine.data import PROJECT_ROOT, load_player_stats, load_players, load_snap_counts
from fantasy_projection_engine.opp_eff import COMPONENTS, add_components
from fantasy_projection_engine.player_games import build_player_games
from fantasy_projection_engine.tuning import K, tune_opp_eff


def main():
    g = add_components(prepare_games(build_player_games(load_player_stats(), load_snap_counts(), load_players())))
    params, grid = tune_opp_eff(g, DEV_SEASONS)
    lines = [f"# Opportunity × efficiency tuning (dev {DEV_SEASONS[0]}–{DEV_SEASONS[-1]})", ""]
    for c in COMPONENTS:
        p = params[c]
        lines += [f"## {c}: hl_vol={p.hl_vol}, hl_eff={p.hl_eff}, k={p.k} (MSE {grid[c][0][0]:.4f})", ""]
        ks = {r[3]: r[0] for r in grid[c] if (r[1], r[2], r[4], r[5]) == (p.hl_vol, p.hl_eff, p.hl_long, p.m)}
        lines += ["MSE vs k at best half-lives: " + ", ".join(f"k={k}: {ks[k]:.4f}" for k in K), ""]
    lines += [f"## other: hl={params['other_hl']}"]
    out = {c: asdict(params[c]) for c in COMPONENTS} | {"other_hl": params["other_hl"]}
    (PROJECT_ROOT / "reports" / "tune_opp_eff.md").write_text("\n".join(lines))
    (PROJECT_ROOT / "reports" / "opp_eff_params.json").write_text(json.dumps(out, indent=2))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
