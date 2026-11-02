"""Experiment: floor / median / ceiling, simple version (v9). Dev seasons only.

Pre-registered (DECISIONS.md, 2026-11-02):
  floor / ceiling = b10_pos / b90_pos × proj_v5 (quantile regression through origin, walk-forward)
  benchmark       = the same method on the baseline projection
  Pass: Big-60 coverage 77–83% with each tail 7–13%, AND interval score < benchmark (p < 0.05).
  Diagnostics: coverage by position and by pre-game volatility tercile.

Usage: uv run python scripts/exp_intervals.py
"""

import numpy as np
import pandas as pd

from fantasy_projection_engine import DEV_SEASONS
from fantasy_projection_engine.baseline import add_projection, big60_pool
from fantasy_projection_engine.calibration import median_calibration
from fantasy_projection_engine.data import PROJECT_ROOT
from fantasy_projection_engine.metrics import coverage, interval_score, paired_bootstrap
from fantasy_projection_engine.opp_eff import project
from fantasy_projection_engine.tuning import VOL_SHRINK_V2, relevant_mask, tune_baseline, tune_opp_eff

from exp_betting_lines import load_games
from exp_eff_lines import with_eff_adj

TAUS = {"lo": 0.1, "med": 0.5, "hi": 0.9}


def add_volatility(g: pd.DataFrame) -> pd.Series:
    """Coefficient of variation of the player's previous 16 games (pre-game info only)."""
    past = g.groupby("player_id")["actual"].shift(1)
    roll = past.groupby(g["player_id"]).rolling(16, min_periods=6)
    sd = roll.std().reset_index(level=0, drop=True)
    mu = roll.mean().reset_index(level=0, drop=True)
    return (sd / mu.where(mu > 1)).reindex(g.index)


def bands(fold, col, rel, prefix):
    for k, tau in TAUS.items():
        fold[f"{prefix}_{k}"], t = median_calibration(fold, col, rel, "lad_mult", tau=tau)
        yield k, t


def cov_row(label, d, p):
    c = coverage(d["actual"], d[f"{p}_lo"], d[f"{p}_hi"])
    return f"| {label} | {len(d)} | {100 * c['inside']:.1f}% | {100 * c['below']:.1f}% | {100 * c['above']:.1f}% |"


def main():
    g = load_games()
    g["cv"] = add_volatility(g)
    rel = relevant_mask(g)
    cache, folds, coefs = {}, [], []
    for s in DEV_SEASONS[1:]:
        train = [t for t in DEV_SEASONS if t < s]
        fold = add_projection(g, tune_baseline(g, train), "proj_base")
        v4, _ = tune_opp_eff(g, train, cache, VOL_SHRINK_V2, rel, team=True, lines=True)
        fold["raw"] = project(g, with_eff_adj(v4, "lines"), cache)["proj"].to_numpy()
        for name, col in [("m", "raw"), ("b", "proj_base")]:
            for k, t in bands(fold, col, rel, name):
                if name == "m":
                    coefs += [(s, r.position, k, r.b) for r in t[t["season"] == s].itertuples()]
        folds.append(fold[fold["season"] == s])
    df = pd.concat(folds, ignore_index=True).dropna(subset=["m_med", "b_med", "m_lo", "m_hi", "b_lo", "b_hi"])
    df["cluster"] = df["season"].astype(str) + "-" + df["week"].astype(str)
    big = df.loc[big60_pool(df, "proj_base").index.union(big60_pool(df, "m_med").index)].copy()
    for d in (big, df):
        d["is_m"] = interval_score(d["actual"], d["m_lo"], d["m_hi"])
        d["is_b"] = interval_score(d["actual"], d["b_lo"], d["b_hi"])

    c = pd.DataFrame(coefs, columns=["season", "position", "q", "b"]).pivot_table(index=["season", "position"], columns="q", values="b")
    L = ["# Experiment: floor / median / ceiling, simple version (v9), forward-chained OOS 2020–2023", "",
         "## Fitted percentages of the mean projection (from seasons 2019..s−1)", "",
         "| season | position | floor (10th) | median (50th) | ceiling (90th) |", "|---|---|---|---|---|"]
    L += [f"| {s} | {p} | {100 * r['lo']:.0f}% | {100 * r['med']:.0f}% | {100 * r['hi']:.0f}% |" for (s, p), r in c.iterrows()]
    L += ["", "## Calibration (target: 80% inside, 10% below, 10% above)", "",
          "| pool | n | inside | below floor | above ceiling |", "|---|---|---|---|---|",
          cov_row("**Big-60, v9**", big, "m"), cov_row("Big-60, benchmark (baseline-centred)", big, "b"),
          cov_row("All players, v9", df, "m")]
    for p in ["QB", "RB", "WR", "TE"]:
        L.append(cov_row(f"Big-60 {p}, v9", big[big.position == p], "m"))
    terc = pd.qcut(big["cv"], 3, labels=["steady (low CV)", "middle", "volatile (high CV)"])
    for t in terc.cat.categories:
        L.append(cov_row(f"Big-60 {t}, v9", big[terc == t], "m"))
    L.append(cov_row("Big-60 no volatility history (< 6 games)", big[big["cv"].isna()], "m"))
    L += ["", "## Interval score (lower = better; paired, week-clustered bootstrap)", "",
          "| pool | n | v9 | benchmark | diff | 95% CI | p(v9 not better) |", "|---|---|---|---|---|---|---|"]
    for name, d in {"big60": big, "all": df}.items():
        r = paired_bootstrap(d["is_m"], d["is_b"], d["cluster"])
        L.append(f"| {name} | {len(d)} | {d['is_m'].mean():.3f} | {d['is_b'].mean():.3f} | {r['diff']:+.3f} | "
                 f"[{r['ci_low']:+.3f}, {r['ci_high']:+.3f}] | {r['p_a_not_better']:.3f} |")
    L += ["", "## Average interval width, Big-60 (points)", "", "| model | floor | median | ceiling | width |", "|---|---|---|---|---|"]
    for p, label in [("m", "v9"), ("b", "benchmark")]:
        L.append(f"| {label} | {big[f'{p}_lo'].mean():.1f} | {big[f'{p}_med'].mean():.1f} | {big[f'{p}_hi'].mean():.1f} | "
                 f"{(big[f'{p}_hi'] - big[f'{p}_lo']).mean():.1f} |")
    (PROJECT_ROOT / "reports" / "exp_intervals.md").write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
