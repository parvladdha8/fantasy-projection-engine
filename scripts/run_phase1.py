"""Phase 1 end-to-end: (optionally) download data, run quality checks, score baselines.

Usage:
    uv run python scripts/run_phase1.py            # use cached data
    uv run python scripts/run_phase1.py --refresh  # re-download first

Writes reports/phase1_report.md. Scores DEV seasons only (2019–2023);
2024 validation and 2025 test are deliberately NOT scored here.
"""

import sys

import pandas as pd

from fantasy_projection_engine import DEV_SEASONS
from fantasy_projection_engine.baseline import METHODS, add_projection, big60_pool, prepare_games, score
from fantasy_projection_engine.data import PROJECT_ROOT, load_player_stats, load_schedules, pull_raw
from fantasy_projection_engine.quality import run_all


def md_table(df: pd.DataFrame, index: bool = False) -> str:
    """Tiny markdown-table writer (avoids an extra dependency)."""
    if index:
        df = df.reset_index().rename(columns={"index": ""})
    fmt = lambda v: f"{v:.3f}" if isinstance(v, float) else str(v)  # noqa: E731
    head = "| " + " | ".join(map(str, df.columns)) + " |"
    sep = "|" + "---|" * len(df.columns)
    body = ["| " + " | ".join(fmt(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join([head, sep, *body])


def main():
    if "--refresh" in sys.argv:
        pull_raw()
    ps, sched = load_player_stats(), load_schedules()

    lines = ["# Phase 1 report", "", "## Data-quality checks", ""]
    checks = run_all(ps, sched)
    for c in checks:
        lines.append(f"- **{'PASS' if c['passed'] else 'FAIL'}**: {c['name']}. {c['detail']}")

    games = prepare_games(ps)
    rows = []
    by_pos = {}
    for m in METHODS:
        g = add_projection(games, m)
        dev = g[g["season"].isin(DEV_SEASONS)]
        for pool_name, pool in [("all", dev), ("big60", big60_pool(dev))]:
            rows.append({"method": m, "pool": pool_name, **score(pool)})
            if pool_name == "big60":
                by_pos[m] = {p: score(pool[pool["position"] == p])["mae"] for p in ["QB", "RB", "WR", "TE"]}
    res = pd.DataFrame(rows)

    lines += ["", f"## Baseline variants, development seasons {DEV_SEASONS[0]}–{DEV_SEASONS[-1]}", ""]
    for pool_name in ["big60", "all"]:
        t = res[res["pool"] == pool_name].sort_values("mae").drop(columns="pool")
        lines += [f"### Pool: {pool_name}", "", md_table(t), ""]
    lines += ["### Big-60 pool MAE by position", "", md_table(pd.DataFrame(by_pos).T.sort_values("WR"), index=True), ""]

    out = PROJECT_ROOT / "reports" / "phase1_report.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(lines))
    print("\n".join(lines))
    print(f"\nWrote {out}")
    if not all(c["passed"] for c in checks):
        sys.exit("Some data-quality checks FAILED: review before trusting results.")


if __name__ == "__main__":
    main()
