"""Checks the single prediction function on REAL data (development seasons only) and shows examples.

  1. No look-ahead: projections for 2023 week 10 are identical whether or not any later game
     (rest of 2023, all of 2024 and 2025) exists in the data.
  2. Same model as validated: the mean projection equals the frozen v5 model used for 2024.
  3. The waterfall adds up: baseline + Σ deltas = median for every explainable player-game.
  4. Example explanations: 2023 week 10's top projections per position (a dev season).

Nothing is tuned or scored here; 2025 rows are never returned (predict's default).

Usage: uv run python scripts/check_predict.py
"""

import numpy as np

from fantasy_projection_engine.data import PROJECT_ROOT
from fantasy_projection_engine.opp_eff import project
from fantasy_projection_engine.predict import STEPS, load_games, load_model, predict

SEASON, WEEK = 2023, 10
COLS = ["median", "floor", "ceiling"] + [f"step_{k}" for k, _ in STEPS]


def main():
    g = load_games()
    full = predict(g)
    cut = g[(g["season"] < SEASON) | ((g["season"] == SEASON) & (g["week"] <= WEEK))].reset_index(drop=True)
    short = predict(cut)
    wk = lambda d: d[(d.season == SEASON) & (d.week == WEEK)].set_index("player_id")[COLS].sort_index()
    a, b = wk(full), wk(short)
    leak = float(np.nanmax(np.abs(a.to_numpy() - b.to_numpy())))
    same_nan = bool((a.isna() == b.isna()).all().all())

    raw = project(g, load_model()["params"])["proj"].to_numpy()[g["season"].isin(full["season"].unique()).to_numpy()]
    same_model = bool(np.allclose(full["step_lines_eff"], raw, equal_nan=True))

    d = full[full["season"] <= 2023]
    ok = d[[f"step_{k}" for k, _ in STEPS]].notna().all(axis=1)
    tele = float(np.abs(d.loc[ok, [f"delta_{k}" for k, _ in STEPS]].sum(axis=1) - d.loc[ok, "median"]).max())

    L = ["# Prediction function check (real data, development seasons only)", "",
         "| check | result |", "|---|---|",
         f"| 1. No look-ahead: {SEASON} week {WEEK} with vs without every later game ({len(a)} players) | "
         f"max difference {leak:.1e} points, same missing values: {same_nan} → {'PASS' if leak < 1e-9 and same_nan else 'FAIL'} |",
         f"| 2. Mean projection = frozen v5 (the model validated on 2024) | {'PASS' if same_model else 'FAIL'} |",
         f"| 3. Waterfall adds up to the median ({ok.sum():,} player-games, 2018–2023) | max error {tele:.1e} → "
         f"{'PASS' if tele < 1e-9 else 'FAIL'} |",
         f"| Coverage of the explanation | {ok.mean():.1%} of player-games (the rest are first career games: no history) |", "",
         "## Average size of each step, 2020–2023, by position (points; descriptive)", "",
         "| position | " + " | ".join(lbl for _, lbl in STEPS[1:]) + " |", "|---|" + "---|" * (len(STEPS) - 1)]
    dd = d[d.season >= 2020]
    for pos in ["QB", "RB", "WR", "TE"]:
        x = dd[dd.position == pos]
        L.append(f"| {pos} | " + " | ".join(f"{x[f'delta_{k}'].mean():+.2f} (±{x[f'delta_{k}'].abs().mean():.2f})"
                                             for k, _ in STEPS[1:]) + " |")
    L += ["", "Each cell: average change (average size of the change). A step can matter a lot for individual "
          "players while averaging near zero.", "",
          f"## Examples: {SEASON} week {WEEK}, top 3 median projections per position", ""]
    ex = full[(full.season == SEASON) & (full.week == WEEK)]
    for pos in ["QB", "RB", "WR", "TE"]:
        for r in ex[ex.position == pos].nlargest(3, "median").itertuples():
            L.append(f"- **{r.player_display_name}** ({pos}, {r.team}), actual {r.actual:.1f}: {r.explanation}")
            parts = [f"{c}: {getattr(r, f'vol_{c}'):.1f} {u} × {getattr(r, f'eff_{c}'):.2f} pts "
                     f"(share {100 * getattr(r, f'share_{c}'):.0f}% of {getattr(r, f'team_vol_{c}'):.1f}; "
                     f"efficiency {100 * getattr(r, f'shrink_{c}'):.0f}% shrunk to league average)"
                     for c, u in [("rec", "targets"), ("rush", "carries"), ("pass", "attempts")]
                     if getattr(r, f"proj_{c}") > 0.5]
            L.append("  - " + "; ".join(parts))
    for out in (PROJECT_ROOT / "reports" / "predict_check.md", PROJECT_ROOT / "paper" / "check_predict.md"):
        out.write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
