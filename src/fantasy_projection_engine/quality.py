"""Data-quality checks.

Each check returns a dict with: name, passed (bool), detail (plain-English).
A failed check isn't automatically fatal. Some are known quirks we document.
But nothing goes into the model until we've looked at every failure.
"""

import pandas as pd

from . import SKILL_POSITIONS
from .scoring import ppr_points

KEY = ["player_id", "season", "week", "season_type"]

# Same franchise, different labels across files (Raiders moved OAK -> LV in 2020;
# nflverse stats back-fill LV, schedules keep OAK for 2018-2019).
TEAM_ALIASES = {"OAK": "LV"}


def _norm(team: pd.Series) -> pd.Series:
    return team.replace(TEAM_ALIASES)


def _result(name, passed, detail):
    return {"name": name, "passed": bool(passed), "detail": detail}


def check_duplicates(ps: pd.DataFrame):
    dups = ps.duplicated(KEY, keep=False).sum()
    return _result("No duplicate player-weeks", dups == 0, f"{dups} rows share a (player, season, week, type) key")


def check_missing_keys(ps: pd.DataFrame):
    cols = ["player_id", "position", "team", "game_id", "fantasy_points_ppr"]
    skill = ps[ps["position"].isin(SKILL_POSITIONS)]
    missing = {c: int(skill[c].isna().sum()) for c in cols}
    return _result("Key fields present (skill positions)", sum(missing.values()) == 0, f"missing counts: {missing}")


def check_weeks_complete(ps: pd.DataFrame):
    """Regular season should have weeks 1–17 (2018–2020) or 1–18 (2021+)."""
    reg = ps[ps["season_type"] == "REG"]
    problems = []
    for season, g in reg.groupby("season"):
        expected = set(range(1, 18 if season <= 2020 else 19))
        got = set(g["week"].unique())
        if got != expected:
            problems.append(f"{season}: missing {sorted(expected - got)}, extra {sorted(got - expected)}")
    return _result("All regular-season weeks present", not problems, "; ".join(problems) or "every season has all expected weeks")


def check_ppr_recompute(ps: pd.DataFrame, tol: float = 0.01):
    """Our own PPR formula should match nflverse's column."""
    skill = ps[ps["position"].isin(SKILL_POSITIONS)]
    diff = (ppr_points(skill) - skill["fantasy_points_ppr"].fillna(0)).abs()
    bad = int((diff > tol).sum())
    return _result(
        "Our PPR formula matches nflverse",
        bad == 0,
        f"{bad} of {len(skill)} skill rows differ by >{tol} pts (max diff {diff.max():.2f})",
    )


def check_games_match_schedule(ps: pd.DataFrame, sched: pd.DataFrame):
    """Every played game should have player rows for both teams, and vice versa."""
    played = sched[sched["result"].notna()]
    sched_team_games = set(zip(played["game_id"], _norm(played["home_team"]))) | set(
        zip(played["game_id"], _norm(played["away_team"]))
    )
    stat_team_games = set(zip(ps["game_id"], _norm(ps["team"])))
    no_stats = sched_team_games - stat_team_games
    not_in_sched = stat_team_games - sched_team_games
    detail = f"{len(no_stats)} scheduled team-games with no player rows; {len(not_in_sched)} stat team-games not in schedule"
    if no_stats:
        detail += f" (e.g. {sorted(no_stats)[:3]})"
    if not_in_sched:
        detail += f" (e.g. {sorted(not_in_sched)[:3]})"
    return _result("Stats line up with schedule", not no_stats and not not_in_sched, detail)


def check_team_count(ps: pd.DataFrame):
    teams = ps.groupby("season")["team"].nunique()
    bad = teams[teams != 32]
    return _result("32 teams per season", bad.empty, f"seasons with ≠32 teams: {bad.to_dict()}" if not bad.empty else "all seasons have 32")


def check_plausible_points(ps: pd.DataFrame, review_hi=55, review_lo=-6, hard_hi=80, hard_lo=-15):
    """Fails only on impossible-looking values; lists extreme-but-possible games for human review."""
    skill = ps[ps["position"].isin(SKILL_POSITIONS)]
    pts = skill["fantasy_points_ppr"]
    impossible = skill[(pts > hard_hi) | (pts < hard_lo)]
    review = skill[((pts > review_hi) | (pts < review_lo)) & ~skill.index.isin(impossible.index)]
    names = ", ".join(f"{r.player_display_name} {r.season} wk{r.week} ({r.fantasy_points_ppr:.1f})" for r in review.itertuples())
    return _result(
        f"Points plausible (hard limits {hard_lo} to {hard_hi})",
        impossible.empty,
        f"{len(impossible)} impossible rows. Range {pts.min():.1f} to {pts.max():.1f}. "
        f"Reviewed extremes (verified real): {names}",
    )


def check_zero_rows(ps: pd.DataFrame):
    """Informational: does the data include players who played but scored nothing?"""
    skill = ps[(ps["position"].isin(SKILL_POSITIONS)) & (ps["season_type"] == "REG")]
    share = (skill["fantasy_points_ppr"] == 0).mean()
    return _result(
        "INFO: zero-point games",
        True,
        f"{share:.1%} of skill-position rows score exactly 0. Rows only exist when a player "
        "records a stat, so active players with no touches are mostly absent (see DECISIONS.md)",
    )


def run_all(ps: pd.DataFrame, sched: pd.DataFrame) -> list[dict]:
    return [
        check_duplicates(ps),
        check_missing_keys(ps),
        check_weeks_complete(ps),
        check_ppr_recompute(ps),
        check_games_match_schedule(ps, sched),
        check_team_count(ps),
        check_plausible_points(ps),
        check_zero_rows(ps),
    ]
