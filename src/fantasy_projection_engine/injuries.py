"""Injury reports → absent teammates → vacated opportunity (v7).

Absent = designated Out or Doubtful on the final pre-kickoff injury report (≈ 99% miss the game).
Entries modified after kickoff are ignored (no look-ahead).

For a player i on team T in week w (component c = rec / rush):
    V_same  = Σ vacated shares of absent teammates at i's position
    V_other = Σ vacated shares of absent teammates at other positions
    share′  = share × (1 + λ_same · V_same + λ_other · V_other)
An absent player's vacated share = his shrunk share of team volume as of his most recent game
for team T (this season or last). λ is fitted walk-forward by season (seasons < s only).
"""

import numpy as np
import pandas as pd

ABSENT_STATUSES = ("Out", "Doubtful")
TEAM_ALIASES = {"OAK": "LV"}
SKILL = ("QB", "RB", "WR", "TE")


def kickoffs(schedules: pd.DataFrame) -> pd.DataFrame:
    """Kickoff time (UTC) per team-game. nflverse game times are US Eastern."""
    s = schedules[schedules["game_type"] == "REG"]
    kick = pd.to_datetime(s["gameday"] + " " + s["gametime"]).dt.tz_localize("America/New_York").dt.tz_convert("UTC")
    out = [pd.DataFrame({"season": s["season"], "week": s["week"], "team": s[f"{side}_team"].replace(TEAM_ALIASES),
                         "kickoff": kick}) for side in ("home", "away")]
    return pd.concat(out, ignore_index=True)


def build_absences(injuries: pd.DataFrame, schedules: pd.DataFrame) -> pd.DataFrame:
    """One row per (player_id, team, season, week) designated Out/Doubtful before kickoff."""
    i = injuries[(injuries["game_type"] == "REG") & injuries["position"].isin(SKILL)
                 & injuries["report_status"].isin(ABSENT_STATUSES)].copy()
    i["season"], i["week"] = i["season"].astype(int), i["week"].astype(int)
    i["team"] = i["team"].replace(TEAM_ALIASES)
    i = i.merge(kickoffs(schedules), on=["season", "week", "team"], how="inner")
    i = i[i["date_modified"] <= i["kickoff"]]  # only what was known at kickoff
    i = i.rename(columns={"gsis_id": "player_id"})
    return i[["player_id", "team", "season", "week", "report_status"]].drop_duplicates(["player_id", "season", "week"])


def link_absences(d: pd.DataFrame, absences: pd.DataFrame) -> pd.DataFrame:
    """Attach to each absence the row position (in d) of that player's latest earlier game for the
    same team, this season or the previous one. Absences with no such game are dropped."""
    g = d[["player_id", "team", "season", "week", "position"]].reset_index(drop=True)
    g["row"] = np.arange(len(g))
    g["t"] = g["season"] * 100 + g["week"]
    a = absences.assign(t=absences["season"] * 100 + absences["week"]).reset_index(drop=True)
    a["aid"] = np.arange(len(a))
    m = a.merge(g[["player_id", "team", "t", "season", "row", "position"]], on=["player_id", "team"],
                suffixes=("", "_game"))
    m = m[(m["t_game"] < m["t"]) & (m["season_game"] >= m["season"] - 1)]
    m = m.sort_values("t_game").groupby("aid").tail(1)
    return m[["player_id", "team", "season", "week", "position", "row"]].reset_index(drop=True)


def vacated(d: pd.DataFrame, links: pd.DataFrame, share_post: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(V_same, V_other) per row of d, from absent teammates' post-game shares. Excludes the player himself."""
    l = links.assign(v=np.nan_to_num(share_post[links["row"].to_numpy()]))
    key = ["team", "season", "week"]
    by_pos = l.groupby(key + ["position"], as_index=False)["v"].sum().rename(columns={"v": "v_pos"})
    tot = l.groupby(key, as_index=False)["v"].sum().rename(columns={"v": "v_tot"})
    own = l[key + ["player_id", "v"]].rename(columns={"v": "v_self"})
    r = d[key + ["position", "player_id"]].reset_index(drop=True)
    r = r.merge(by_pos, on=key + ["position"], how="left").merge(tot, on=key, how="left") \
         .merge(own, on=key + ["player_id"], how="left").fillna({"v_pos": 0, "v_tot": 0, "v_self": 0})
    same = r["v_pos"] - r["v_self"]
    return same.to_numpy(), (r["v_tot"] - r["v_pos"]).to_numpy()


def vacated_multiplier(d: pd.DataFrame, opp_col: str, base: np.ndarray, v_same: np.ndarray, v_other: np.ndarray,
                       first_season: int | None = None) -> tuple[np.ndarray, list[tuple]]:
    """Walk-forward λ fit:  opp − base = λ_same·(base·V_same) + λ_other·(base·V_other),  base = share × team volume.

    Returns the multiplier (1 + λ_same·V_same + λ_other·V_other; 1 where no earlier data) and
    [(season, λ_same, λ_other)].
    """
    seasons = d["season"].to_numpy()
    y = d[opp_col].to_numpy(float) - base
    X = np.column_stack([base * v_same, base * v_other])
    ok = np.isfinite(base) & np.isfinite(y)
    if first_season is not None:
        ok &= seasons >= first_season
    mult, coefs = np.ones(len(d)), []
    for s in np.unique(seasons):
        train = ok & (seasons < s)
        if train.sum() < 50 or not (X[train] != 0).any():
            continue
        lam = np.linalg.lstsq(X[train], y[train], rcond=None)[0]
        here = seasons == s
        mult[here] = 1 + lam[0] * v_same[here] + lam[1] * v_other[here]
        coefs.append((int(s), float(lam[0]), float(lam[1])))
    return mult, coefs
