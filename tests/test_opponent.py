"""Tests for opponent strength by position (v14): opponent parsing, placebo, shrinkage math, no look-ahead."""

import numpy as np
import pandas as pd
import pytest

from fantasy_projection_engine.opponent import (hyperparams, matchup_table, opponent_multiplier, opponents,
                                                placebo_opponents)

TEAMS = [f"T{i:02d}" for i in range(16)]


def _league(effect=0.0, seasons=(2020, 2021, 2022), weeks=17, seed=0, noise=0.5):
    """16 teams, round-robin pairs each week; 4 TEs per team-game. Defense T00 gives TEs (1+effect)× their median."""
    rng = np.random.default_rng(seed)
    rows = []
    for s in seasons:
        for w in range(1, weeks + 1):
            order = rng.permutation(TEAMS)
            for a, h in zip(order[::2], order[1::2]):
                gid = f"{s}_{w:02d}_{a}_{h}"
                for team, opp in [(a, h), (h, a)]:
                    med = rng.uniform(5, 12, 4)
                    mult = 1 + (effect if opp == "T00" else 0)
                    act = np.maximum(med * mult * rng.lognormal(0, noise, 4), 0)
                    for i in range(4):
                        rows.append({"player_id": f"{team}_{i}", "team": team, "position": "TE", "season": s, "week": w,
                                     "game_id": gid, "actual": act[i], "med": med[i]})
    return pd.DataFrame(rows)


def test_opponents_handles_relocation_alias():
    d = pd.DataFrame({"game_id": ["2018_01_LA_OAK", "2018_01_LA_OAK", "2022_03_KC_BUF"], "team": ["LV", "LA", "BUF"]})
    assert opponents(d).tolist() == ["LA", "LV", "KC"]
    with pytest.raises(ValueError):
        opponents(pd.DataFrame({"game_id": ["2022_03_KC_BUF"], "team": ["NE"]}))


def test_placebo_never_real_or_self_and_consistent_per_team_week():
    d = _league(seasons=(2021,), weeks=3)
    opp = opponents(d)
    fake = placebo_opponents(d, opp, seed=1)
    assert not (fake == opp).any() and not (fake == d["team"].to_numpy()).any()
    assert (pd.Series(fake).groupby([d["week"], d["team"]]).nunique() == 1).all()


def test_no_effect_shrinks_to_zero():
    d = _league(effect=0.0)
    mult, hp, eff = opponent_multiplier(d, "med", np.ones(len(d), bool), opponents(d))
    assert (mult[d.season == 2020] == 1).all()            # no earlier season → no adjustment
    assert np.abs(mult - 1).max() < 0.05                   # pure noise → tiny effects
    assert eff.loc[d.season > 2020, "B"].mean() > 0.7      # ... because they are mostly shrunk away


def test_real_effect_is_recovered_and_lightly_shrunk():
    d = _league(effect=0.4, noise=0.3)
    mult, hp, eff = opponent_multiplier(d, "med", np.ones(len(d), bool), opponents(d))
    late = (d.season == 2022).to_numpy() & (d.week > 4).to_numpy()
    vs0 = late & (opponents(d) == "T00")
    assert np.median(mult[vs0]) - 1 == pytest.approx(0.4 * 15 / 16, abs=0.08)  # relative to league ratio
    assert np.abs(np.median(mult[late & ~vs0]) - 1) < 0.05
    assert hp["tau2"].iloc[-1] > 0


def test_no_look_ahead():
    d = _league(effect=0.3)
    full = opponent_multiplier(d, "med", np.ones(len(d), bool), opponents(d))[0]
    cut = (d.season < 2022) | ((d.season == 2022) & (d.week <= 9))
    d2 = d.copy()
    d2.loc[~cut, "actual"] = 0.0                            # scramble the future
    part = opponent_multiplier(d2, "med", np.ones(len(d2), bool), opponents(d2))[0]
    upto = ((d.season < 2022) | ((d.season == 2022) & (d.week <= 9))).to_numpy()
    assert np.allclose(full[upto], part[upto])


def test_hyperparams_centered_on_league_ratio():
    d = _league(effect=0.0)
    tab = matchup_table(d, "med", np.ones(len(d), bool), opponents(d))
    hp = hyperparams(tab)
    assert hp["R"].iloc[0] == pytest.approx(np.exp(0.5 ** 2 / 2), rel=0.05)  # lognormal mean > median
    assert hp["sigma2"].iloc[0] > 0
