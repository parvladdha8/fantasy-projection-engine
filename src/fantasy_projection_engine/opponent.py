"""Opponent strength by position ("defense vs position"), schedule-adjusted and EB-shrunk (v14).

Pre-registered in DECISIONS.md (2026-11-02). A defense is measured by how much the players it faced beat or
missed their own pre-game median (so who they faced is already accounted for), relative to the league-wide
ratio, decayed over its earlier games (half-life 8 defense-games), then shrunk toward 0 per position:

    raw_d,p  = (Σ λ·A / Σ λ·M) / R_p − 1         A, M = actual and median points of relevant players vs d
    var      = σ²_p · Σ λ²·M / (Σ λ·M)² / R_p²    (per-game noise σ²_p / M)
    B        = var / (var + τ²_p),   δ = (1 − B) · raw,   v14 median = v8m median × (1 + δ)

σ²_p, τ²_p and R_p come only from seasons first_season..s−1; the decayed sums use only games before the week.
"""

import numpy as np
import pandas as pd

from .situational import FIRST_CALIBRATED_SEASON

HALF_LIFE = 8  # defense-games; fixed in advance, not tuned
ALIASES = {"OAK": "LV", "SD": "LAC", "STL": "LA"}  # game_id uses the old abbreviation in early seasons


def opponents(df: pd.DataFrame) -> np.ndarray:
    """The other team in each row's game (game_id = SEASON_WEEK_AWAY_HOME)."""
    p = df["game_id"].str.split("_", expand=True)
    away, home = p[2].replace(ALIASES), p[3].replace(ALIASES)
    team = df["team"].replace(ALIASES)
    if not ((team == away) | (team == home)).all():
        raise ValueError("team not found in its game_id")
    return np.where(team == home, away, home)


def placebo_opponents(df: pd.DataFrame, opp: np.ndarray, seed: int = 0) -> np.ndarray:
    """Placebo: in each season-week, every team gets a random OTHER team's defense (never its own, never the real one
    when avoidable), fixed seed. Same for all of a team's rows in that week."""
    rng = np.random.default_rng(seed)
    tw = pd.DataFrame({"season": df["season"].to_numpy(), "week": df["week"].to_numpy(),
                       "team": df["team"].replace(ALIASES).to_numpy(), "opp": opp}).drop_duplicates(["season", "week", "team"])
    fake = {}
    for (s, w), a in tw.groupby(["season", "week"]):
        teams, real = a["team"].to_numpy(), a["opp"].to_numpy()
        for _ in range(1000):
            perm = rng.permutation(real)
            if not ((perm == teams) | (perm == real)).any():
                break
        fake.update({(s, w, t): o for t, o in zip(teams, perm)})
    keys = zip(df["season"], df["week"], df["team"].replace(ALIASES))
    return np.array([fake[k] for k in keys])


def matchup_table(df: pd.DataFrame, med_col: str, fit_mask: np.ndarray, opp: np.ndarray,
                  first_season: int = FIRST_CALIBRATED_SEASON) -> pd.DataFrame:
    """One row per (defense, position, game): A = Σ actual, M = Σ median of relevant players facing it."""
    x, y = df[med_col].to_numpy(float), df["actual"].to_numpy(float)
    ok = fit_mask & np.isfinite(x) & np.isfinite(y) & (x > 0) & (df["season"].to_numpy() >= first_season)
    d = pd.DataFrame({"defense": opp[ok], "position": df["position"].to_numpy()[ok], "season": df["season"].to_numpy()[ok],
                      "week": df["week"].to_numpy()[ok], "game_id": df["game_id"].to_numpy()[ok], "A": y[ok], "M": x[ok]})
    t = d.groupby(["defense", "position", "season", "week", "game_id"], as_index=False)[["A", "M"]].sum()
    t["t"] = (t["season"] * 100 + t["week"]).astype("int64")
    return t.sort_values(["defense", "position", "t"], ignore_index=True)


def hyperparams(tab: pd.DataFrame) -> pd.DataFrame:
    """Per position: league ratio R, per-game noise σ² (per unit of expected points), true spread τ² across defenses."""
    out = []
    for p, a in tab.groupby("position"):
        R = a["A"].sum() / a["M"].sum()
        ds = a.groupby(["defense", "season"]).agg(A=("A", "sum"), M=("M", "sum"), n=("A", "size")).reset_index()
        a = a.merge(ds[["defense", "season", "A", "M"]].rename(columns={"A": "A_ds", "M": "M_ds"}), on=["defense", "season"])
        g, gbar = a["A"] / a["M"] - 1, a["A_ds"] / a["M_ds"] - 1
        sigma2 = float((a["M"] * (g - gbar) ** 2).sum() / max(len(a) - len(ds), 1))
        Rs = ds.groupby("season")[["A", "M"]].transform("sum")
        dev = (ds["A"] / ds["M"]) / (Rs["A"] / Rs["M"]) - 1
        noise = sigma2 / ds["M"] / (Rs["A"] / Rs["M"]) ** 2
        tau2 = max(0.0, float((dev ** 2).mean() - noise.mean()))
        out.append({"position": p, "R": R, "sigma2": sigma2, "tau2": tau2, "defense_seasons": len(ds)})
    return pd.DataFrame(out)


def _pre_game_sums(tab: pd.DataFrame, hl: float) -> pd.DataFrame:
    """For each (defense, position) game: decayed sums of the games strictly BEFORE it... returned as the state
    AFTER each game (so a later target looks up the last state with t' < t)."""
    lam = 0.5 ** (1 / hl)
    rows = []
    for (d, p), a in tab.groupby(["defense", "position"], sort=False):
        SA = SM = S2 = 0.0
        for t, A, M in zip(a["t"], a["A"], a["M"]):
            SA, SM, S2 = A + lam * SA, M + lam * SM, M + lam ** 2 * S2
            rows.append((d, p, t, SA, SM, S2))
    return pd.DataFrame(rows, columns=["defense", "position", "t", "SA", "SM", "S2"])


def opponent_multiplier(df: pd.DataFrame, med_col: str, fit_mask: np.ndarray, opp: np.ndarray,
                        first_season: int = FIRST_CALIBRATED_SEASON, hl: float = HALF_LIFE
                        ) -> tuple[np.ndarray, pd.DataFrame, pd.DataFrame]:
    """Walk-forward v14 multiplier. Returns (mult, hyperparameter table per season, per-row effects)."""
    tab = matchup_table(df, med_col, fit_mask, opp, first_season)
    state = _pre_game_sums(tab, hl).sort_values("t", kind="stable")
    tgt = pd.DataFrame({"row": np.arange(len(df)), "defense": opp, "position": df["position"].to_numpy(),
                        "season": df["season"].to_numpy(),
                        "t": (df["season"].to_numpy() * 100 + df["week"].to_numpy()).astype("int64")})
    tgt = pd.merge_asof(tgt.sort_values("t", kind="stable"), state, on="t", by=["defense", "position"],
                        allow_exact_matches=False).sort_values("row")
    mult, delta, Bcol = np.ones(len(df)), np.zeros(len(df)), np.ones(len(df))
    htabs = []
    for s in np.unique(tgt["season"]):
        hp = hyperparams(tab[tab["season"] < s])
        if hp.empty:
            continue
        htabs.append(hp.assign(season=s))
        a = tgt[(tgt["season"] == s) & tgt["SM"].gt(0)].merge(hp, on="position")
        raw = (a["SA"] / a["SM"]) / a["R"] - 1
        var = a["sigma2"] * a["S2"] / a["SM"] ** 2 / a["R"] ** 2
        B = np.where(a["tau2"] > 0, var / (var + a["tau2"]), 1.0)
        i = a["row"].to_numpy()
        delta[i], Bcol[i] = (1 - B) * raw, B
        mult[i] = 1 + delta[i]
    eff = pd.DataFrame({"defense": opp, "position": df["position"].to_numpy(), "season": df["season"].to_numpy(),
                        "week": df["week"].to_numpy(), "delta": delta, "B": Bcol})
    return mult, (pd.concat(htabs, ignore_index=True) if htabs else pd.DataFrame()), eff
