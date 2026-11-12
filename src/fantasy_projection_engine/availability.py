"""Injury status and chance of playing, from the official NFL injury reports (nflverse `load_injuries`).

Why this exists (DECISIONS.md 2026-11-11, "Injury status always current"): the free report for week W arrives team by
team from Wednesday to Friday. Before a team's week-W report exists, its most recent report is LAST week's, so a player
ruled Out last week must not look healthy just because this week's report isn't out yet. We carry his last status
forward, clearly labelled, until his team's new report replaces it.

Projections stay conditional on playing (that is how the Big 60 grades them: inactive players are removed for every
source). The chance of playing is shown next to them. It is an observed frequency from 2018–2023 (development
seasons only), not a guess: of all past players in the same report state, the share who then played.

States (a player has at most one; healthy players have none):
  this week's report (team has published week W):
    out, doubtful, questionable       game designation (Friday; Out players are removed from the projections)
    dnp, limited, full                listed in practice with no game designation (yet)
  carried forward (team has NOT published week W yet; its latest earlier report said):
    prev_out, prev_doubtful           ruled Out / Doubtful for his team's previous game
  latest news (Sleeper's player status, which updates within hours; DECISIONS.md 2026-11-11, "Second injury source"):
    news_out, news_doubtful, news_questionable, ir, pup, suspended, not_active
    Used whenever the team's official week-W report has no game designation for him yet. No chance-of-playing
    figure: we have no history of Sleeper's mid-week statuses to measure one from.
"""

import json
from pathlib import Path

import pandas as pd

RATES_FILE = Path(__file__).resolve().parents[2] / "reports" / "availability.json"
# Practice-only states (dnp/limited/full) get no chance-of-playing figure: history only keeps each week's FINAL report,
# so a Wednesday "did not practice" can't be matched to past Wednesdays. Their text is still shown.
RATED = ("out", "doubtful", "questionable", "prev_out", "prev_doubtful")


def load_rates() -> dict:
    r = json.loads(RATES_FILE.read_text())["p_play"]
    return {k: v for k, v in r.items() if k in RATED}

LABEL = {
    "out": "Out", "doubtful": "Doubtful", "questionable": "Questionable",
    "dnp": "Did not practice", "limited": "Limited in practice", "full": "Full practice",
    "prev_out": "Out last game", "prev_doubtful": "Doubtful last game",
    "news_out": "Out", "news_doubtful": "Doubtful", "news_questionable": "Questionable",
    "ir": "Injured reserve", "pup": "PUP list", "suspended": "Suspended", "not_active": "Not active",
}
CARRIED = ("prev_out", "prev_doubtful")
SLEEPER_STATE = {"Out": "news_out", "Doubtful": "news_doubtful", "Questionable": "news_questionable", "IR": "ir",
                 "PUP": "pup", "Sus": "suspended", "NA": "not_active", "DNR": "not_active"}
NEWS = tuple(sorted(set(SLEEPER_STATE.values())))
DESIGNATED = ("out", "doubtful", "questionable")   # official game designations: always win over news


def _practice(s: pd.Series) -> pd.Series:
    s = s.fillna("").str.lower()
    return pd.Series(pd.NA, index=s.index, dtype="object").mask(s.str.contains("did not"), "dnp") \
        .mask(s.str.contains("limited"), "limited").mask(s.str.contains("full"), "full")


def _report_state(rows: pd.DataFrame) -> pd.Series:
    """State from a team-week report row: the game designation if any, else the practice participation."""
    d = rows["report_status"].fillna("").str.lower().map({"out": "out", "doubtful": "doubtful", "questionable": "questionable"})
    return d.fillna(_practice(rows["practice_status"]))


def injury_states(injuries: pd.DataFrame, season: int, week: int) -> pd.DataFrame:
    """Latest known injury state for (season, week). Returns player_id, team, state, injury, report_week, carried.
    Uses only reports for weeks <= `week`, so it never looks ahead."""
    i = injuries[(injuries["season"] == season) & (injuries["game_type"] == "REG") & (injuries["week"] <= week)].copy()
    if i.empty:
        return pd.DataFrame({"player_id": [], "team": [], "state": [], "injury": [], "report_week": [],
                             "carried": pd.Series([], dtype=bool)})
    i["state"] = _report_state(i)
    i["injury"] = i["report_primary_injury"].fillna(i["practice_primary_injury"])
    cur_teams = set(i.loc[i["week"] == week, "team"])
    cur = i[(i["week"] == week)].dropna(subset=["state"])
    # Teams without a week-W report yet: their most recent earlier report (skips bye weeks), Out/Doubtful only.
    earlier = i[(i["week"] < week) & ~i["team"].isin(cur_teams)]
    last_wk = earlier.groupby("team")["week"].transform("max")
    prev = earlier[(earlier["week"] == last_wk) & earlier["state"].isin(["out", "doubtful"])].copy()
    prev["state"] = "prev_" + prev["state"]
    out = pd.concat([cur.assign(carried=False), prev.assign(carried=True)], ignore_index=True)
    out = out.rename(columns={"gsis_id": "player_id", "week": "report_week"}).dropna(subset=["player_id"])
    out["carried"] = out["carried"].astype(bool)   # an empty concat would leave it as object, breaking ~carried
    return out.drop_duplicates("player_id", keep="first")[["player_id", "team", "state", "injury", "report_week", "carried"]]


def sleeper_states(raw: list[dict], sleeper_to_gsis: pd.DataFrame) -> pd.DataFrame:
    """Injury states from Sleeper's player records (the `player` object in its projections feed, already fetched once
    per refresh). sleeper_to_gsis: columns sleeper_id, gsis_id. Same columns as injury_states, plus source."""
    xw = sleeper_to_gsis.dropna().astype({"sleeper_id": str}).drop_duplicates("sleeper_id").set_index("sleeper_id")["gsis_id"]
    rows = []
    for x in raw:
        pl = x.get("player") or {}
        state, gid = SLEEPER_STATE.get(pl.get("injury_status") or ""), xw.get(str(x.get("player_id")))
        if state and gid:
            injury = " ".join(t for t in (pl.get("injury_body_part"), (pl.get("injury_notes") or "").lower()) if t) or None
            rows.append({"player_id": gid, "team": x.get("team"), "state": state, "injury": injury,
                         "report_week": pd.NA, "carried": False, "source": "sleeper"})
    cols = ["player_id", "team", "state", "injury", "report_week", "carried", "source"]
    return pd.DataFrame(rows, columns=cols).drop_duplicates("player_id")


def combine_states(official: pd.DataFrame, news: pd.DataFrame) -> pd.DataFrame:
    """One state per player. The official week-W game designation (Out/Doubtful/Questionable) always wins; otherwise
    the latest news wins over practice-only lines and last week's carried status, because it is more recent; with no
    news, the official/carried state stays (we never clear an injury just because one source is silent)."""
    off = official.assign(source="nfl")
    final = off[off["state"].isin(DESIGNATED) & ~off["carried"]]
    rest_news = news[~news["player_id"].isin(final["player_id"])]
    rest_off = off[~off["player_id"].isin(final["player_id"]) & ~off["player_id"].isin(rest_news["player_id"])]
    return pd.concat([final, rest_news, rest_off], ignore_index=True)


def estimate_play_rates(injuries: pd.DataFrame, played_by_week: dict, rosters_weekly: pd.DataFrame,
                        seasons, positions=("QB", "RB", "WR", "TE")) -> pd.DataFrame:
    """Share of players in each state who played that week, pooled over `seasons` (use development seasons only).
    played_by_week[(season, week)] = set of player_ids with a stat line or an offensive snap.

    Two information moments, matching what the live site can know:
      - this-week states: the team's final week-W report (what exists by kickoff);
      - carried states: the team's previous report, as seen BEFORE its week-W report exists (Mon–Wed).
    Players on reserve/practice squad/cut at week W are left out, because live projections drop them anyway."""
    rows = []
    for season in seasons:
        inj = injuries[(injuries["season"] == season) & (injuries["position"].isin(positions))]
        rw = rosters_weekly[(rosters_weekly["season"] == season) & (rosters_weekly["game_type"] == "REG")]
        for week in sorted(inj.loc[inj["game_type"] == "REG", "week"].unique()):
            played = played_by_week.get((season, int(week)))
            if played is None:
                continue
            gone = set(rw.loc[(rw["week"] == week) & rw["status"].isin(["RES", "DEV", "CUT", "RET"]), "gsis_id"])
            cur = injury_states(inj, season, int(week))
            cur = cur[cur["carried"].eq(False)]
            before = injury_states(inj[~((inj["week"] == week))], season, int(week))   # as on Monday: no week-W report
            before = before[before["carried"].eq(True)]
            for df in (cur, before):
                df = df[~df["player_id"].isin(gone)]
                rows.append(pd.DataFrame({"state": df["state"], "played": df["player_id"].isin(played)}))
    d = pd.concat(rows, ignore_index=True)
    r = d.groupby("state")["played"].agg(n="size", played="sum").reset_index()
    r["p_play"] = r["played"] / r["n"]
    return r


def attach_status(players: pd.DataFrame, states: pd.DataFrame, rates: dict) -> pd.DataFrame:
    """Add injury_state, injury_status (display text) and p_play to a table with player_id. Healthy → NaN."""
    s = states.reindex(columns=["player_id", "state", "injury", "report_week", "carried", "source"])
    out = players.merge(s, on="player_id", how="left")
    def text(r):
        if pd.isna(r["state"]):
            return None
        t = LABEL[r["state"]]
        if r["carried"]:
            t += f" (week {int(r['report_week'])}); this week's report not out yet"
        elif r.get("source") == "sleeper":
            t += ", per latest news (Sleeper); official report not out yet"
        if isinstance(r["injury"], str) and r["injury"]:
            t += f" · {r['injury']}"
        return t
    out["injury_status"] = out.apply(text, axis=1)
    out["p_play"] = out["state"].map(rates)
    return out.rename(columns={"state": "injury_state"}).drop(columns=["injury", "report_week", "carried", "source"])
