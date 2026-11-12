"""Tests for injury absences and vacated opportunity."""

import numpy as np
import pandas as pd
import pytest

from fantasy_projection_engine.injuries import build_absences, link_absences, vacated, vacated_multiplier


def _sched():
    return pd.DataFrame({"game_type": ["REG"], "season": [2020], "week": [3], "gameday": ["2020-09-27"],
                         "gametime": ["13:00"], "home_team": ["KC"], "away_team": ["OAK"]})


def _inj(modified):
    return pd.DataFrame({"game_type": "REG", "position": ["WR", "WR", "RB"], "season": 2020.0, "week": 3.0,
                         "team": ["KC", "KC", "OAK"], "gsis_id": ["a", "b", "c"],
                         "report_status": ["Out", "Questionable", "Doubtful"],
                         "date_modified": pd.to_datetime(modified, utc=True)})


def test_absences_use_only_pre_kickoff_out_or_doubtful():
    # kickoff 13:00 ET = 17:00 UTC. Player c's entry was modified after kickoff → ignored.
    a = build_absences(_inj(["2020-09-25 20:00", "2020-09-25 20:00", "2020-09-27 18:00"]), _sched())
    assert a["player_id"].tolist() == ["a"]                         # b is only Questionable
    a2 = build_absences(_inj(["2020-09-25 20:00"] * 3), _sched())
    assert set(a2["player_id"]) == {"a", "c"} and (a2.loc[a2.player_id == "c", "team"] == "LV").all()


def _games():
    return pd.DataFrame({"player_id": ["a", "a", "a", "x", "x", "y"], "team": ["KC", "KC", "NYJ", "KC", "KC", "KC"],
                         "season": [2019, 2020, 2020, 2020, 2020, 2020], "week": [10, 1, 2, 1, 3, 3],
                         "position": ["WR", "WR", "WR", "WR", "WR", "TE"]})


def test_link_uses_latest_earlier_game_for_same_team():
    d = _games()
    l = link_absences(d, pd.DataFrame({"player_id": ["a"], "team": ["KC"], "season": [2020], "week": [3]}))
    assert l["row"].tolist() == [1]          # 2020 wk 1 for KC (wk 2 was for NYJ → not KC's share)


def test_vacated_split_by_position_and_excludes_self():
    d = _games()
    links = pd.DataFrame({"player_id": ["a", "x"], "team": "KC", "season": 2020, "week": 3,
                          "position": "WR", "row": [1, 3]})
    share_post = np.array([0, 0.25, 0, 0.10, 0, 0])
    same, other = vacated(d, links, share_post)
    # row 4 = x himself (listed but played): only a's 0.25 counts as same-position vacated
    assert same[4] == pytest.approx(0.25) and other[4] == pytest.approx(0)
    # row 5 = TE y: both WRs' shares are "other position"
    assert same[5] == pytest.approx(0) and other[5] == pytest.approx(0.35)


def test_multiplier_recovers_lambda_and_is_walk_forward():
    rng = np.random.default_rng(0)
    n = 9000
    d = pd.DataFrame({"season": rng.choice([2018, 2019, 2020], n)})
    base = rng.uniform(1, 10, n)
    vs = np.where(rng.random(n) < 0.2, rng.uniform(0, 0.3, n), 0)
    vo = np.where(rng.random(n) < 0.2, rng.uniform(0, 0.3, n), 0)
    d["opp"] = base * (1 + 1.2 * vs + 0.3 * vo) + rng.normal(0, 1, n)
    m, coefs = vacated_multiplier(d, "opp", base, vs, vo)
    lam = {s: (a, b) for s, a, b in coefs}
    assert lam[2020][0] == pytest.approx(1.2, abs=0.1) and lam[2020][1] == pytest.approx(0.3, abs=0.1)
    assert np.all(m[(d.season == 2018).to_numpy()] == 1)
    assert np.all(m[vs + vo == 0] == 1)                     # no absences → untouched
    d2 = d.copy()
    d2.loc[d2.season == 2020, "opp"] *= 4
    np.testing.assert_allclose(vacated_multiplier(d2, "opp", base, vs, vo)[0], m)


def test_post_game_state_equals_next_game_prior():
    from fantasy_projection_engine.opp_eff import _dsum, _dsum_post
    d = pd.DataFrame({"player_id": ["a"] * 4 + ["b"] * 3, "targets": [5, 7, 2, 9, 1, 4, 6]})
    cache = {}
    prior, post = _dsum(d, "targets", 4, cache), _dsum_post(d, "targets", 4, cache)
    np.testing.assert_allclose(post[[0, 1, 2, 4, 5]], prior[[1, 2, 3, 5, 6]])


# --- Live injury status (availability.py; DECISIONS.md 2026-11-11) -------------------------------------------------
def _report(rows):
    base = {"season": 2026, "game_type": "REG", "report_primary_injury": None, "practice_primary_injury": None,
            "practice_status": None, "report_status": None, "position": "WR"}
    return pd.DataFrame([{**base, **r} for r in rows])


def test_out_last_week_is_carried_until_team_reports():
    from fantasy_projection_engine.availability import injury_states
    inj = _report([
        {"team": "NE", "week": 9, "gsis_id": "brown", "report_status": "Out", "report_primary_injury": "Hamstring"},
        {"team": "NE", "week": 9, "gsis_id": "q1", "report_status": "Questionable"},      # not carried (only Out/Doubtful)
        {"team": "NYG", "week": 9, "gsis_id": "nab", "report_status": "Out"},
        {"team": "NYG", "week": 10, "gsis_id": "nab", "practice_status": "Full Participation in Practice"},
    ])
    s = injury_states(inj, 2026, 10).set_index("player_id")
    assert s.loc["brown", "state"] == "prev_out" and bool(s.loc["brown", "carried"]) and s.loc["brown", "report_week"] == 9
    assert "q1" not in s.index
    assert s.loc["nab", "state"] == "full" and not bool(s.loc["nab", "carried"])   # NYG's week-10 report replaces week 9


def test_bye_week_carries_from_last_report_and_no_lookahead():
    from fantasy_projection_engine.availability import injury_states
    inj = _report([{"team": "KC", "week": 8, "gsis_id": "x", "report_status": "Doubtful"},     # KC bye in week 9
                {"team": "KC", "week": 11, "gsis_id": "x", "report_status": "Out"}])        # future report: never used
    s = injury_states(inj, 2026, 10).set_index("player_id")
    assert s.loc["x", "state"] == "prev_doubtful" and s.loc["x", "report_week"] == 8


def test_attach_status_text_and_rates():
    from fantasy_projection_engine.availability import attach_status, injury_states
    inj = _report([{"team": "NE", "week": 9, "gsis_id": "brown", "report_status": "Out", "report_primary_injury": "Hamstring"}])
    out = attach_status(pd.DataFrame({"player_id": ["brown", "healthy"]}), injury_states(inj, 2026, 10), {"prev_out": 0.31})
    b, h = out.set_index("player_id").loc["brown"], out.set_index("player_id").loc["healthy"]
    assert b["injury_status"] == "Out last game (week 9); this week's report not out yet · Hamstring" and b["p_play"] == 0.31
    assert pd.isna(h["injury_status"]) and pd.isna(h["p_play"])


def test_play_rates_count_only_listed_players():
    from fantasy_projection_engine.availability import estimate_play_rates
    inj = _report([{"team": "NE", "week": 1, "gsis_id": "a", "report_status": "Out"},
                {"team": "NE", "week": 2, "gsis_id": "b", "report_status": "Questionable"},
                {"team": "NE", "week": 2, "gsis_id": "c", "report_status": "Questionable"}])
    rw = pd.DataFrame({"season": [2026], "game_type": ["REG"], "week": [2], "status": ["ACT"], "gsis_id": ["a"]})
    r = estimate_play_rates(inj, {(2026, 1): set(), (2026, 2): {"a", "b"}}, rw, [2026]).set_index("state")
    assert r.loc["out", "p_play"] == 0.0                     # a: Out week 1, didn't play
    assert r.loc["prev_out", "p_play"] == 1.0                # a: Out week 1 → played week 2 (seen Monday, before week-2 report)
    assert r.loc["questionable", "p_play"] == 0.5            # b played, c didn't


def _sleeper(pid, status, part=None, notes=None, team="LAR"):
    return {"player_id": pid, "team": team, "player": {"injury_status": status, "injury_body_part": part, "injury_notes": notes}}


def test_sleeper_news_flags_player_before_official_report():
    """Puka Nacua, Nov 11 2026: Sleeper had him Out (MCL) while the Rams' week-10 report wasn't on nflverse yet."""
    from fantasy_projection_engine.availability import attach_status, combine_states, injury_states, sleeper_states
    xw = pd.DataFrame({"sleeper_id": ["s1", "s2", "s3", "s4"], "gsis_id": ["puka", "ir_guy", "q_off", "healthy"]})
    raw = [_sleeper("s1", "Out", "Knee - MCL", "Sprain"), _sleeper("s2", "IR", "Ankle"),
           _sleeper("s3", "Out"), _sleeper("s4", None)]
    official = injury_states(_report([{"team": "LA", "week": 10, "gsis_id": "q_off", "report_status": "Questionable"}]), 2026, 10)
    out = attach_status(pd.DataFrame({"player_id": ["puka", "ir_guy", "q_off", "healthy"]}),
                        combine_states(official, sleeper_states(raw, xw)), {"questionable": 0.66}).set_index("player_id")
    assert out.loc["puka", "injury_status"] == "Out, per latest news (Sleeper); official report not out yet · Knee - MCL sprain"
    assert out.loc["puka", "injury_state"] == "news_out" and pd.isna(out.loc["puka", "p_play"])   # no history → no %
    assert out.loc["ir_guy", "injury_status"].startswith("Injured reserve")
    assert out.loc["q_off", "injury_state"] == "questionable" and out.loc["q_off", "p_play"] == 0.66  # official designation wins
    assert pd.isna(out.loc["healthy", "injury_status"])


def test_news_beats_carried_and_practice_but_silence_never_clears():
    from fantasy_projection_engine.availability import combine_states, injury_states, sleeper_states
    official = injury_states(_report([
        {"team": "NE", "week": 9, "gsis_id": "carried", "report_status": "Out"},
        {"team": "NE", "week": 9, "gsis_id": "still_carried", "report_status": "Out"},
        {"team": "NYG", "week": 10, "gsis_id": "dnp", "practice_status": "Did Not Participate In Practice"}]), 2026, 10)
    xw = pd.DataFrame({"sleeper_id": ["a", "b"], "gsis_id": ["carried", "dnp"]})
    s = combine_states(official, sleeper_states([_sleeper("a", "Questionable"), _sleeper("b", "Doubtful")], xw)).set_index("player_id")
    assert s.loc["carried", "state"] == "news_questionable"   # newer news replaces last week's Out
    assert s.loc["dnp", "state"] == "news_doubtful"           # and a practice-only line
    assert s.loc["still_carried", "state"] == "prev_out"      # no news → last week's Out stays
    assert len(s) == 3


def test_sleeper_cache_reused_within_window(tmp_path, monkeypatch):
    from fantasy_projection_engine import consensus
    calls = []
    monkeypatch.setattr(consensus, "fetch_sleeper", lambda season, week: calls.append(1) or [{"x": 1}])
    a = consensus.fetch_sleeper_cached(tmp_path, 2026, 10, "2026-11-11T21:00:00Z")
    b = consensus.fetch_sleeper_cached(tmp_path, 2026, 10, "2026-11-11T21:10:00Z")   # snapshot step: reuse
    c = consensus.fetch_sleeper_cached(tmp_path, 2026, 10, "2026-11-11T23:00:00Z")   # stale: fetch again
    assert len(calls) == 2 and a == b == ([{"x": 1}], "2026-11-11T21:00:00Z") and c[1] == "2026-11-11T23:00:00Z"


# --- First-start QBs (debuts.py; DECISIONS.md 2026-11-12) ----------------------------------------------------------
def _qb_sched():
    return pd.DataFrame([
        {"game_id": "g1", "season": 2026, "week": 9, "game_type": "REG", "home_team": "MIA", "away_team": "BUF", "home_qb_id": "willis", "away_qb_id": "allen", "home_score": 20},
        {"game_id": "g2", "season": 2026, "week": 10, "game_type": "REG", "home_team": "MIA", "away_team": "NYJ", "home_qb_id": "mccord", "away_qb_id": "vet", "home_score": None},
        {"game_id": "g3", "season": 2026, "week": 10, "game_type": "REG", "home_team": "ARI", "away_team": "SF", "home_qb_id": None, "away_qb_id": None, "home_score": None}])


def test_debut_rows_only_unprojected_never_started_active_qb1s():
    from fantasy_projection_engine.debuts import debut_rows
    qb1 = pd.DataFrame({"team": ["MIA", "ARI", "SF", "BUF", "NYJ"], "player_id": ["mccord", "beck", "projected", "allen", "old"]})
    roster = pd.DataFrame({"player_id": ["mccord", "beck", "projected", "allen", "old"], "team": ["MIA", "ARI", "SF", "BUF", "NYJ"],
                           "status": ["ACT", "ACT", "ACT", "ACT", "ACT"]})
    players = pd.DataFrame({"gsis_id": ["mccord", "beck", "projected", "allen", "old"], "display_name": ["Kyle McCord", "Carson Beck", "P", "Josh Allen", "Old Vet"],
                            "rookie_season": [2026, 2026, 2020, 2018, 2010]})
    est = {"floor": 2.0, "median": 11.9, "ceiling": 21.7}
    r = debut_rows(qb1, roster, ["projected"], _qb_sched(), players, 2026, 10, est).set_index("player_id")
    # mccord: listed starter in an UNPLAYED game, which must not count as a past start (no look-ahead)
    assert set(r.index) == {"mccord", "beck"}     # allen: BUF is on bye and has started; old: pre-2018 career; projected: model has him
    assert r.loc["mccord", "game_id"] == "g2" and r.loc["beck", "median"] == 11.9 and pd.isna(r.loc["beck", "step_baseline"])


def test_first_starts_and_validation():
    from fantasy_projection_engine.debuts import estimate, first_starts, validate
    s = _qb_sched().assign(home_score=1)
    pg = pd.DataFrame({"game_id": ["g1", "g2"], "player_id": ["willis", "mccord"], "fantasy_points_ppr": [10.0, 20.0]})
    players = pd.DataFrame({"gsis_id": ["willis", "mccord", "allen", "vet"], "rookie_season": [2022, 2026, 2018, 2015]})
    f = first_starts(s, pg, players).set_index("player_id")
    assert set(f.index) == {"willis", "mccord", "allen"} and f.loc["allen", "fantasy_points_ppr"] == 0.0   # no stat line → 0
    est = estimate(f.reset_index(), [2026])
    assert est["n"] == 3 and est["median"] == 10.0
    v = validate(f.reset_index(), {"median": 10.0, "floor": 5.0, "ceiling": 15.0}, 2026)
    assert v["mae"] == (0 + 10 + 10) / 3 and v["coverage"] == 1 / 3
