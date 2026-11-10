"""Tests for live grading: inactive rules, readiness, provisional window, and re-scoring overwrites cleanly."""

import pandas as pd

from fantasy_projection_engine.grading import actual_points, evidence_of_play, inactive_players, is_final, week_ready
from fantasy_projection_engine.leaderboard import score_week
from fantasy_projection_engine.storage import connect_sqlite, save_grading


def test_inactive_rules():
    roster = pd.DataFrame({"gsis_id": ["act0", "ina", "res", "dev_up", "out"],
                           "status": ["ACT", "INA", "RES", "DEV", "INA"]})
    played = {"dev_up"}                      # practice-squad elevation who recorded a catch
    ids = ["act0", "ina", "res", "dev_up", "out", "gone"]   # "gone": no roster row that week (released)
    inact = inactive_players(ids, played, roster, out_ids={"out"}).set_index("player_id")["reason"].to_dict()
    assert inact == {"ina": "inactive_at_kickoff", "res": "inactive_at_kickoff", "out": "designated_out",
                     "gone": "inactive_at_kickoff"}
    # act0 dressed and did nothing: ACTIVE (scores 0); dev_up played: active despite DEV status


def test_evidence_of_play_uses_stats_or_offensive_snaps():
    stats = pd.DataFrame({"season": [2026], "week": [9], "player_id": ["a"]})
    snaps = pd.DataFrame({"season": [2026, 2026], "week": [9, 9], "pfr_player_id": ["PB", "PC"], "offense_snaps": [3, 0]})
    players = pd.DataFrame({"gsis_id": ["b", "c"], "pfr_id": ["PB", "PC"]})
    assert evidence_of_play(stats, snaps, players, 2026, 9) == {"a", "b"}


def _sched(final=True):
    return pd.DataFrame({"season": 2026, "week": 9, "game_type": "REG", "home_team": ["AAA", "CCC"], "away_team": ["BBB", "DDD"],
                         "home_score": [21.0, 17.0 if final else None], "gameday": ["2026-11-08", "2026-11-09"]})


def test_week_ready_requires_final_games_stats_and_rosters():
    stats = pd.DataFrame({"season": [2026], "week": [9], "player_id": ["a"]})
    rost = pd.DataFrame({"season": 2026, "week": 9, "team": ["AAA", "BBB", "CCC", "DDD"]})
    assert week_ready(_sched(final=False), stats, rost, 2026, 9)[0] is False
    assert week_ready(_sched(), stats.iloc[:0], rost, 2026, 9)[0] is False
    assert week_ready(_sched(), stats, rost.iloc[:3], 2026, 9)[0] is False
    assert week_ready(_sched(), stats, rost, 2026, 9) == (True, "ready")


def test_provisional_for_ten_days_after_last_game():
    assert not is_final(_sched(), 2026, 9, "2026-11-19T12:00:00Z")
    assert is_final(_sched(), 2026, 9, "2026-11-20T00:00:00Z")


def test_rescoring_replaces_provisional_result():
    c = connect_sqlite()
    frozen = pd.DataFrame({"player_id": ["p1", "p2"], "game_id": "G", "position": "QB", "projected": [20.0, 15.0]})
    ours = frozen.assign(projected=[18.0, 16.0])
    for pts in ([18.0, 10.0], [22.0, 10.0]):          # second pass: a stat correction for p1
        stats = pd.DataFrame({"season": 2026, "week": 9, "player_id": ["p1", "p2"], "fantasy_points_ppr": pts})
        act = actual_points(stats, frozen, 2026, 9)
        w, pos, _ = score_week(frozen, ours, act, platform="baseline")
        save_grading(c, 2026, 9, act, pd.DataFrame(columns=["player_id", "game_id", "reason"]), [w], pos, now="2026-11-10T15:00:00Z")
    assert c.execute("SELECT COUNT(*) FROM actuals").fetchone()[0] == 2
    assert c.execute("SELECT points_ppr FROM actuals WHERE player_id = 'p1'").fetchone()[0] == 22.0
    lb = c.execute("SELECT mae_ours, mae_platform, winner FROM leaderboard_weekly").fetchall()
    assert lb == [(5.0, 3.5, "platform")]   # ours |18−22|,|16−10| → 5.0; baseline |20−22|,|15−10| → 3.5


def test_highlights_saved_and_replaced_on_rescore():
    from fantasy_projection_engine.leaderboard import highlights
    c = connect_sqlite()
    frozen = pd.DataFrame({"player_id": ["p1", "p2"], "game_id": "G", "position": "QB", "projected": [20.0, 15.0]})
    ours = frozen.assign(projected=[18.0, 16.0])
    stats = pd.DataFrame({"season": 2026, "week": 9, "player_id": ["p1", "p2"], "fantasy_points_ppr": [18.0, 10.0]})
    act = actual_points(stats, frozen, 2026, 9)
    w, pos, scored = score_week(frozen, ours, act, platform="sleeper")
    h = highlights(scored, "sleeper").assign(player_name=["One", "Two"])
    for _ in range(2):   # re-scoring must not duplicate rows
        save_grading(c, 2026, 9, act, pd.DataFrame(columns=["player_id", "game_id", "reason"]), [w], pos,
                     now="2026-11-10T15:00:00Z", highlights=h)
    rows = c.execute("SELECT kind, rank, player_name FROM leaderboard_highlights ORDER BY kind").fetchall()
    assert rows == [("loss", 1, "Two"), ("win", 1, "One")]   # p1: ours 0 vs theirs 2 → win; p2: 6 vs 5 → loss
