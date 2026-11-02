"""ONE-TIME validation on the 2024 season (CLAUDE.md rigor rule 4).

The model is frozen BEFORE this runs: settings come from reports/opp_eff_params.json (tuned on
2019–2023 only) and the baseline method is tuned on 2019–2023 only. Nothing is tuned on 2024.
Every 2024 projection uses only data from before that game's kickoff (walk-forward);
2025 is never scored.

Writes reports/validation_2024.md. Refuses to run twice (the validation season is used once);
the guard can only be overridden with --i-understand-this-reuses-2024.

Usage: uv run python scripts/validate_2024.py
"""

import json
import sys

import numpy as np
import pandas as pd

from fantasy_projection_engine import DEV_SEASONS, VALIDATION_SEASON as VALIDATION
from fantasy_projection_engine.baseline import BIG60_SLOTS, add_projection, big60_pool, score
from fantasy_projection_engine.data import PROJECT_ROOT
from fantasy_projection_engine.metrics import mae, paired_bootstrap
from fantasy_projection_engine.opp_eff import COMPONENTS, CompParams, project
from fantasy_projection_engine.tuning import tune_baseline

from exp_betting_lines import load_games

OUT = PROJECT_ROOT / "reports" / "validation_2024.md"


def load_frozen_params() -> dict:
    raw = json.loads((PROJECT_ROOT / "reports" / "opp_eff_params.json").read_text())
    return {c: CompParams(**raw[c]) for c in COMPONENTS} | {"other_hl": raw["other_hl"]}


def head_to_head(df: pd.DataFrame, pool_col: str) -> tuple[list[str], int, int]:
    """Weekly Big-60 duel on the pool selected by `pool_col`'s own projections."""
    rows, w, l = [], 0, 0
    pool = big60_pool(df, pool_col)
    for wk, d in pool.groupby("week"):
        a, b = mae(d["actual"], d["proj_model"]), mae(d["actual"], d["proj_base"])
        w, l = w + (a < b), l + (a >= b)
        rows.append(f"| {wk} | {a:.2f} | {b:.2f} | {'model' if a < b else 'baseline'} | {w}–{l} |")
    return rows, w, l


def main():
    if OUT.exists() and "--i-understand-this-reuses-2024" not in sys.argv:
        sys.exit(f"{OUT.name} already exists: 2024 has been used for validation. Not re-running.")
    params = load_frozen_params()
    g = load_games()
    method = tune_baseline(g, DEV_SEASONS)
    df = add_projection(g, method, "proj_base")
    df["proj_model"] = project(g, params)["proj"].to_numpy()
    df = df[df["season"] == VALIDATION].dropna(subset=["proj_base", "proj_model"])
    assert df["season"].unique().tolist() == [VALIDATION]
    df["cluster"] = df["week"].astype(str)
    big = df.loc[big60_pool(df, "proj_base").index.union(big60_pool(df, "proj_model").index)]

    L = [f"# Validation: season {VALIDATION} (one-time, frozen model)", "",
         f"Model settings: `reports/opp_eff_params.json` (tuned on {DEV_SEASONS[0]}–{DEV_SEASONS[-1]}). "
         f"Baseline: `{method}` (tuned on the same seasons).", "",
         "## Headline (Big-60 = union of both models' own pools)", "",
         "| pool | n | MAE model | MAE baseline | diff | 95% CI | p(model not better) |", "|---|---|---|---|---|---|---|"]
    pools = {"big60": big, "all players": df, **{f"big60 {p}": big[big.position == p] for p in BIG60_SLOTS}}
    for name, d in pools.items():
        r = paired_bootstrap((d["actual"] - d["proj_model"]).abs(), (d["actual"] - d["proj_base"]).abs(), d["cluster"])
        L.append(f"| {name} | {len(d)} | {mae(d['actual'], d['proj_model']):.3f} | {mae(d['actual'], d['proj_base']):.3f} | "
                 f"{r['diff']:+.3f} | [{r['ci_low']:+.3f}, {r['ci_high']:+.3f}] | {r['p_a_not_better']:.3f} |")
    L += ["", "(Per-position rows are descriptive; with only 18 weekly clusters, their CIs are wide.)", "",
          "## Secondary metrics (Big-60 union)", "", "| model | MAE | RMSE | Spearman | bias |", "|---|---|---|---|---|"]
    for m in ["model", "base"]:
        s = score(big, f"proj_{m}")
        L.append(f"| {m} | {s['mae']:.3f} | {s['rmse']:.3f} | {s['spearman']:.3f} | {np.mean(big[f'proj_{m}'] - big['actual']):+.2f} |")
    for label, col in [("baseline's own Big-60 (the CLAUDE.md format: their pool)", "proj_base"),
                       ("our own Big-60", "proj_model")]:
        rows, w, l = head_to_head(df, col)
        L += ["", f"## Weekly head-to-head on the {label}: model {w}–{l}", "",
              "| week | MAE model | MAE baseline | winner | record |", "|---|---|---|---|---|", *rows]
    OUT.write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
