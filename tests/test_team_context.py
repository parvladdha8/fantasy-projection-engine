"""Tests for team-context volume (share × expected team volume)."""

import numpy as np
import pandas as pd
import pytest

from fantasy_projection_engine.opp_eff import DEFAULT_PARAMS, CompParams, add_components, component_arrays
from fantasy_projection_engine.player_games import STAT_COLS
from fantasy_projection_engine.team_context import add_team_totals, build_team_games


def _toy():
    """Player A on KC weeks 1–3 then traded to DEN week 4. Player B on DEN all 4 weeks."""
    rows = []
    plan = [("A", "KC", [5, 10, 6, 4]), ("B", "DEN", [8, 8, 8, 8])]
    for pid, team0, tgts in plan:
        for w, t in enumerate(tgts, start=1):
            team = "DEN" if (pid == "A" and w == 4) else team0
            r = {c: 0.0 for c in STAT_COLS}
            r.update(targets=float(t), receptions=t / 2, receiving_yards=8.0 * t)
            rows.append({"player_id": pid, "position": "WR", "team": team, "season": 2019, "week": w,
                         "game_id": f"2019_{w:02d}_{team}", "season_type": "REG", **r})
    ps = pd.DataFrame(rows)
    # filler teammates so team totals are known: KC 25/50/30/–, DEN 40 every week
    extra = []
    for w, kc in zip([1, 2, 3], [20, 40, 24]):
        extra.append({"team": "KC", "week": w, "targets": float(kc)})
    for w in [1, 2, 3, 4]:
        a_on_den = 4 if w == 4 else 0
        extra.append({"team": "DEN", "week": w, "targets": float(40 - 8 - a_on_den)})
    fill = []
    for e in extra:
        r = {c: 0.0 for c in STAT_COLS}
        r["targets"] = e["targets"]
        fill.append({"player_id": f"F_{e['team']}", "position": "WR", "team": e["team"], "season": 2019,
                     "week": e["week"], "game_id": f"2019_{e['week']:02d}_{e['team']}", "season_type": "REG", **r})
    ps = pd.concat([ps, pd.DataFrame(fill)], ignore_index=True)
    ps["carries"] = 0.0
    ps["attempts"] = 0.0
    tg = build_team_games(ps)
    g = add_team_totals(ps.drop(columns="season_type"), tg)
    g = g.sort_values(["player_id", "season", "week"]).reset_index(drop=True)
    return add_components(g)


def test_team_totals():
    g = _toy()
    kc = g[(g["team"] == "KC")].drop_duplicates("game_id").sort_values("week")["team_targets"].tolist()
    assert kc == [25.0, 50.0, 30.0]
    assert (g.loc[g["team"] == "DEN", "team_targets"] == 40.0).all()


def test_share_times_team_volume_by_hand():
    g = _toy()
    p = CompParams(hl_vol=1e9, hl_eff=8, k=25, team=True, hl_team=1e9)  # huge half-lives = plain averages
    vol, _, _ = component_arrays(g, "rec", p, {})
    a = g.index[(g["player_id"] == "A")]
    # A week 3: share = (5+10)/(25+50) = 0.2; KC's average team targets over weeks 1–2 = 37.5
    assert vol[a[2]] == pytest.approx(0.2 * 37.5)
    # A week 4 (traded to DEN): share over weeks 1–3 = 21/105 = 0.2; DEN team average weeks 1–3 = 40
    assert vol[a[3]] == pytest.approx(0.2 * 40.0)


def test_team_projection_no_lookahead():
    g = _toy()
    p = CompParams(hl_vol=3, hl_eff=8, k=25, team=True, hl_team=4)
    before = component_arrays(g, "rec", p, {})[0]
    g2 = g.copy()
    g2.loc[g2["week"] == 3, ["targets", "team_targets"]] *= 3   # change week 3 for everyone
    after = component_arrays(g2, "rec", p, {})[0]
    m = (g["week"] <= 3).to_numpy()
    np.testing.assert_allclose(before[m], after[m], equal_nan=True)
    assert not np.allclose(before[~m], after[~m])
