"""ONE-TIME final test on the 2025 season (CLAUDE.md rigor rule 4). Pre-registered in DECISIONS.md (2026-11-03).

Runs exactly the live model: predict() with the frozen reports/opp_eff_params.json. Nothing is tuned.
Every 2025 projection uses only data from before that game's kickoff (walk-forward).
Headline: median vs baseline, Big-60 union, week-clustered paired bootstrap; pass = p < 0.05.

Refuses to run twice (writes reports/test_2025.md).

Usage: uv run python scripts/test_2025.py
"""

import sys

import numpy as np

from fantasy_projection_engine import TEST_SEASON
from fantasy_projection_engine.baseline import BIG60_SLOTS, big60_pool, score
from fantasy_projection_engine.data import PROJECT_ROOT
from fantasy_projection_engine.metrics import coverage, mae, paired_bootstrap
from fantasy_projection_engine.predict import load_games, predict

OUT = PROJECT_ROOT / "reports" / "test_2025.md"


def head_to_head(df, pool_col):
    rows, w, l = [], 0, 0
    for wk, d in big60_pool(df, pool_col).groupby("week"):
        a, b = mae(d["actual"], d["median"]), mae(d["actual"], d["step_baseline"])
        w, l = w + (a < b), l + (a >= b)
        rows.append(f"| {wk} | {a:.2f} | {b:.2f} | {'model' if a < b else 'baseline'} | {w}–{l} |")
    return rows, w, l


def boot(name, d, col):
    r = paired_bootstrap((d["actual"] - d[col]).abs(), (d["actual"] - d["step_baseline"]).abs(), d["cluster"])
    return (f"| {name} | {len(d)} | {mae(d['actual'], d[col]):.3f} | {mae(d['actual'], d['step_baseline']):.3f} | "
            f"{r['diff']:+.3f} | [{r['ci_low']:+.3f}, {r['ci_high']:+.3f}] | {r['p_a_not_better']:.3f} |"), r


def main():
    if OUT.exists():
        sys.exit(f"{OUT.name} already exists: 2025 has been used for the final test. Not re-running.")
    pred = predict(load_games(), allow_test=True)
    df = pred[pred["season"] == TEST_SEASON].dropna(subset=["step_baseline", "median", "floor", "ceiling", "actual"]).copy()
    assert df["season"].unique().tolist() == [TEST_SEASON] and len(df) > 1000
    df["cluster"] = df["week"].astype(str)
    big = df.loc[big60_pool(df, "step_baseline").index.union(big60_pool(df, "median").index)]

    head, r = boot("**big60 (headline)**", big, "median")
    verdict = "PASSED" if r["p_a_not_better"] < 0.05 else "FAILED"
    L = [f"# Final test: season {TEST_SEASON} (one-time, frozen live model) — {verdict}", "",
         "Model: `predict()` with `reports/opp_eff_params.json` (tuned 2019–23, validated on 2024). Nothing tuned on 2025.", "",
         "## Median (published projection) vs baseline (Big-60 = union of both pools; clusters = weeks)", "",
         "| pool | n | MAE model | MAE baseline | diff | 95% CI | p(model not better) |", "|---|---|---|---|---|---|---|", head,
         boot("all players", df, "median")[0]]
    L += [boot(f"big60 {p} (descriptive)", big[big.position == p], "median")[0] for p in BIG60_SLOTS]
    L += ["", "## Mean projection (v5) vs baseline (secondary; the 2024 validation's headline)", "",
          "| pool | n | MAE mean | MAE baseline | diff | 95% CI | p |", "|---|---|---|---|---|---|---|",
          boot("big60", big, "step_lines_eff")[0], boot("all players", df, "step_lines_eff")[0]]
    L += ["", "## Secondary metrics (Big-60 union)", "", "| projection | MAE | RMSE | Spearman | bias (proj − actual) |", "|---|---|---|---|---|"]
    for name, col in [("median", "median"), ("mean (v5)", "step_lines_eff"), ("baseline", "step_baseline")]:
        s = score(big, col)
        L.append(f"| {name} | {s['mae']:.3f} | {s['rmse']:.3f} | {s['spearman']:.3f} | {np.mean(big[col] - big['actual']):+.2f} |")
    L += ["", "## Floor–ceiling coverage (target ~80%)", "", "| pool | n | inside | below floor | above ceiling |", "|---|---|---|---|---|"]
    for name, d in [("big60", big), ("all players", df)] + [(f"big60 {p}", big[big.position == p]) for p in BIG60_SLOTS]:
        c = coverage(d["actual"], d["floor"], d["ceiling"])
        L.append(f"| {name} | {len(d)} | {c['inside']:.1%} | {(d.actual < d.floor).mean():.1%} | {(d.actual > d.ceiling).mean():.1%} |")
    for label, col in [("baseline's own Big-60 (the CLAUDE.md format)", "step_baseline"), ("our own Big-60", "median")]:
        rows, w, l = head_to_head(df, col)
        L += ["", f"## Weekly head-to-head on the {label}: model {w}–{l}", "",
              "| week | MAE model | MAE baseline | winner | record |", "|---|---|---|---|---|", *rows]
    OUT.write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
