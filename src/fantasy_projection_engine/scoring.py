"""Full-PPR scoring, computed from raw box-score stats.

We compute points ourselves (instead of trusting a column blindly) so that
(a) we can verify nflverse's numbers, and (b) every source we compare against
is scored with exactly the same rules (rigor rule 5: fair comparison).

Full PPR rules used:
  Passing: 1 pt / 25 yds, 4 per TD, -2 per INT
  Rushing & receiving: 1 pt / 10 yds, 6 per TD, 1 per reception
  2-point conversions (pass, rush, or receive): 2 each
  Fumbles lost (rushing, receiving, sack): -2 each
  Special-teams (return) TDs: 6 each
"""

import pandas as pd


def ppr_points(df: pd.DataFrame) -> pd.Series:
    f = lambda c: df[c].fillna(0)  # noqa: E731 — missing stat = 0 for that stat
    return (
        f("passing_yards") / 25
        + 4 * f("passing_tds")
        - 2 * f("passing_interceptions")
        + f("rushing_yards") / 10
        + 6 * f("rushing_tds")
        + f("receiving_yards") / 10
        + 6 * f("receiving_tds")
        + 1 * f("receptions")
        + 2 * (f("passing_2pt_conversions") + f("rushing_2pt_conversions") + f("receiving_2pt_conversions"))
        - 2 * (f("rushing_fumbles_lost") + f("receiving_fumbles_lost") + f("sack_fumbles_lost"))
        + 6 * f("special_teams_tds")
    )
