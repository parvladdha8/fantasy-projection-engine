"""Big 60 scoring (CLAUDE.md "The Big 60" leaderboard; rules fixed in DECISIONS.md, 2026-11-04).

For each platform and week:
  1. remove players inactive at kickoff (same list for every source; logged);
  2. pool = the PLATFORM's own top 10 QB / 20 RB / 20 WR / 10 TE by its frozen projection (never by actual points);
  3. actual points: active with no stat line = 0;
  4. pool players we have no frozen projection for are dropped from both sides, and counted;
  5. MAE decides the week (equal to 3 decimals = tie); RMSE, Spearman and per-position MAE are reported.
"""

import numpy as np
import pandas as pd

from .baseline import BIG60_SLOTS


def big60(platform_frozen: pd.DataFrame, inactive_ids=()) -> tuple[pd.DataFrame, int]:
    """The platform's own pool: its top-N per position among players NOT inactive at kickoff."""
    p = platform_frozen[~platform_frozen["player_id"].isin(set(inactive_ids))]
    n_inactive = len(platform_frozen) - len(p)
    pool = pd.concat([p[p["position"] == pos].nlargest(n, "projected") for pos, n in BIG60_SLOTS.items()])
    return pool, n_inactive


def _spearman(a, b) -> float:
    if len(a) < 3:
        return float("nan")
    return float(pd.Series(a).rank().corr(pd.Series(b).rank()))


def score_week(platform_frozen: pd.DataFrame, ours_frozen: pd.DataFrame, actuals: pd.DataFrame,
               inactive_ids=(), platform: str = "platform") -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    """Inputs for ONE week: frozen projections (player_id, position, projected) for the platform and for us;
    actuals (player_id, points_ppr). Returns (weekly row, per-position rows, the scored player table)."""
    pool, n_inactive = big60(platform_frozen, inactive_ids)
    ours = ours_frozen[["player_id", "projected"]].rename(columns={"projected": "ours"})
    t = pool.rename(columns={"projected": "theirs"}).merge(ours, on="player_id", how="left")
    t = t.merge(actuals[["player_id", "points_ppr"]], on="player_id", how="left")
    t["actual"] = t["points_ppr"].fillna(0.0)                 # active at kickoff, no stat line → 0
    dropped = int(t["ours"].isna().sum())
    t = t[t["ours"].notna()].copy()
    t["err_ours"], t["err_theirs"] = (t["ours"] - t["actual"]).abs(), (t["theirs"] - t["actual"]).abs()
    mo, mt = t["err_ours"].mean(), t["err_theirs"].mean()
    winner = "tie" if round(mo, 3) == round(mt, 3) else ("ours" if mo < mt else "platform")
    week = {"platform": platform, "n_pool": len(pool), "n_scored": len(t), "n_dropped_no_ours": dropped, "n_inactive": n_inactive,
            "mae_ours": mo, "mae_platform": mt,
            "rmse_ours": float(np.sqrt(((t["ours"] - t["actual"]) ** 2).mean())),
            "rmse_platform": float(np.sqrt(((t["theirs"] - t["actual"]) ** 2).mean())),
            "spearman_ours": _spearman(t["ours"], t["actual"]), "spearman_platform": _spearman(t["theirs"], t["actual"]),
            "winner": winner}
    pos = (t.groupby("position").agg(n=("actual", "size"), mae_ours=("err_ours", "mean"), mae_platform=("err_theirs", "mean"))
           .reset_index().assign(platform=platform))
    return week, pos, t


def season_record(weekly: pd.DataFrame) -> pd.DataFrame:
    """Running W–L–T per platform from weekly rows (winner column), in week order."""
    w = weekly.sort_values(["platform", "season", "week"]).copy()
    for k, lab in [("W", "ours"), ("L", "platform"), ("T", "tie")]:
        w[k] = (w["winner"] == lab).groupby([w["platform"], w["season"]]).cumsum()
    w["record"] = w["W"].astype(str) + "–" + w["L"].astype(str) + w["T"].map(lambda x: f"–{x}" if x else "")
    return w
