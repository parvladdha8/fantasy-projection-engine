"""Proof that live rows have no look-ahead: rebuild past weeks as 'upcoming' from earlier data only and compare
with the full-data projections. Pre-registered requirement (DECISIONS.md, 2026-11-03): exact match.

Usage: uv run python scripts/check_live.py
"""

import numpy as np
import pandas as pd

from fantasy_projection_engine.baseline import big60_pool
from fantasy_projection_engine.data import PROJECT_ROOT, load_player_stats, load_players, load_schedules, load_snap_counts
from fantasy_projection_engine.live import assemble, candidates, played_table
from fantasy_projection_engine.predict import predict

WEEKS = [(2021, 14), (2023, 1), (2023, 10)]
KEY = ["player_id", "game_id"]


def main():
    sch = load_schedules()
    pg = played_table(load_player_stats(), load_snap_counts(), load_players(), sch)
    from fantasy_projection_engine.baseline import prepare_games
    from fantasy_projection_engine.opp_eff import add_components
    full = predict(add_components(prepare_games(pg)), allow_test=True)
    L = ["# Live-row check: past weeks rebuilt as 'upcoming' from earlier data only", "",
         "| week | candidates | played (full data) | matched, same team | max abs diff median | floor | ceiling | "
         "matched but WRONG team | played & not a candidate | of which in Big-60 | candidates who didn't play |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    ok = True
    for s, w in WEEKS:
        before = pg[(pg.season < s) | ((pg.season == s) & (pg.week < w))]
        up = candidates(before, sch, s, w)
        live = predict(assemble(before, up, sch), allow_test=True)
        live = live[(live.season == s) & (live.week == w)]
        ref = full[(full.season == s) & (full.week == w)]
        m = live.merge(ref, on=KEY, suffixes=("_live", "_full"))
        wrong_team = m[m.team_live != m.team_full]
        m = m[m.team_live == m.team_full]  # wrong-team rows are a roster problem, reported separately
        d = {c: np.nanmax(np.abs(m[f"{c}_live"] - m[f"{c}_full"])) for c in ["median", "floor", "ceiling"]}
        nan_mismatch = sum((m[f"{c}_live"].isna() != m[f"{c}_full"].isna()).sum() for c in ["median", "floor", "ceiling"])
        missed = ref[~ref.set_index(KEY).index.isin(live.set_index(KEY).index)]
        big = ref.loc[big60_pool(ref.dropna(subset=["median"]), "median").index]
        missed_big = big[~big.set_index(KEY).index.isin(live.set_index(KEY).index)]
        extra = len(live) - len(m) - len(wrong_team)
        ok &= max(d.values()) < 1e-9 and nan_mismatch == 0
        L.append(f"| {s} wk {w} | {len(live)} | {len(ref)} | {len(m)} | {d['median']:.1e} | {d['floor']:.1e} | {d['ceiling']:.1e} | "
                 f"{len(wrong_team)} | {len(missed)} | {len(missed_big)} | {extra} |")
        if len(missed_big):
            L.append(f"|  | Big-60 players missed: {', '.join(missed_big.player_display_name)} |" + "  |" * 9)
        if len(wrong_team):
            L.append(f"|  | wrong team: {', '.join(wrong_team.player_display_name_live + ' (' + wrong_team.team_live + ' → ' + wrong_team.team_full + ')')} |" + "  |" * 9)
    L += ["", f"**No look-ahead (same-team rows match exactly, ≤ 1e-9, same missing values): {'YES' if ok else 'NO'}**", "",
          "Wrong-team rows and missed players come from roster changes (trades, signings) that game history alone can't see."]
    (PROJECT_ROOT / "reports" / "check_live.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
