"""Situational modifiers (CLAUDE.md model step 3), estimated statistically and shrunk.

Week-of-season effect (v6):
    projection × (1 + γ[position, phase]),  phase = early (wk 1–4) / mid (5–12) / late (13–18)

  raw γ  = (Σ actual − Σ projection) / Σ projection   over fit rows of that cell
  se     = standard error of that ratio  ( sd(actual − projection) · √n / Σ projection )
  Empirical-Bayes shrinkage toward the position's overall γ (normal–normal model):
      τ²  = max(0, variance of the phase γs − mean se²)     between-phase "true" spread
      B   = se² / (se² + τ²)                                share shrunk to the position mean
      γ   = B · γ_pos + (1 − B) · raw γ
  mode="pos" is the control: one γ per position, no phases.

Walk-forward: γ for season s uses fit rows from seasons < s only (seasons ≥ first_season).
"""

import numpy as np
import pandas as pd

PHASES = {"early": (1, 4), "mid": (5, 12), "late": (13, 18)}


def week_phase(week: pd.Series) -> pd.Series:
    return pd.cut(week, bins=[0, 4, 12, 99], labels=list(PHASES)).astype(str)


def _ratio(actual: np.ndarray, proj: np.ndarray) -> tuple[float, float]:
    res = actual - proj
    tot = proj.sum()
    return res.sum() / tot, res.std(ddof=1) * np.sqrt(len(res)) / tot


def fit_week_effects(df: pd.DataFrame, proj_col: str, fit_mask: np.ndarray, mode: str = "phase") -> pd.DataFrame:
    """γ table (position × phase) from the rows in fit_mask. Columns: position, phase, raw, se, B, gamma."""
    d = df[fit_mask].assign(phase=week_phase(df.loc[fit_mask, "week"]))
    rows = []
    for pos, dp in d.groupby("position"):
        g_pos, se_pos = _ratio(dp["actual"].to_numpy(float), dp[proj_col].to_numpy(float))
        if mode == "pos":
            rows += [dict(position=pos, phase=ph, raw=g_pos, se=se_pos, B=np.nan, gamma=g_pos) for ph in PHASES]
            continue
        cells = {ph: _ratio(c["actual"].to_numpy(float), c[proj_col].to_numpy(float)) for ph, c in dp.groupby("phase")}
        raw = np.array([v[0] for v in cells.values()])
        se2 = np.array([v[1] ** 2 for v in cells.values()])
        tau2 = max(0.0, raw.var(ddof=1) - se2.mean()) if len(raw) > 1 else 0.0
        for (ph, (r, se)), s2 in zip(cells.items(), se2):
            B = s2 / (s2 + tau2) if s2 + tau2 > 0 else 1.0
            rows.append(dict(position=pos, phase=ph, raw=r, se=se, B=B, gamma=B * g_pos + (1 - B) * r))
    return pd.DataFrame(rows)


def week_multiplier(df: pd.DataFrame, proj_col: str, fit_mask: np.ndarray, mode: str = "phase",
                    first_season: int = 2019) -> tuple[np.ndarray, pd.DataFrame]:
    """Walk-forward multiplier per row (1 where no earlier data), plus the fitted tables (with 'season')."""
    seasons = df["season"].to_numpy()
    phase = week_phase(df["week"]).to_numpy()
    pos = df["position"].to_numpy()
    ok = fit_mask & np.isfinite(df[proj_col].to_numpy(float)) & np.isfinite(df["actual"].to_numpy(float))
    mult, tables = np.ones(len(df)), []
    for s in np.unique(seasons):
        train = ok & (seasons < s) & (seasons >= first_season)
        if train.sum() < 50:
            continue
        t = fit_week_effects(df, proj_col, train, mode)
        tables.append(t.assign(season=s))
        lookup = {(r.position, r.phase): r.gamma for r in t.itertuples()}
        here = np.flatnonzero(seasons == s)
        mult[here] = 1 + np.array([lookup.get((pos[i], phase[i]), 0.0) for i in here])
    return mult, (pd.concat(tables, ignore_index=True) if tables else pd.DataFrame())


# ---------------------------------------------------------------------------------------------
# Situation effects on the MEDIAN projection: Week 1 (v11 / v11p), prime time (v12 / v12p). See DECISIONS.md (2026-11-02).
#
#   position level  median_w1 = median × (1 + γ_pos)
#       raw γ_pos   LAD through the origin on earlier seasons' Week 1 fit rows: actual ≈ (1+γ)·median
#       se_pos      bootstrap over whole games
#       shrink to 0 τ² = max(0, mean(raw²) − mean(se²)),  B = se²/(se² + τ²),  γ = (1 − B)·raw
#   player level    γ_i = γ_pos + (1 − B_i)·ū_i
#       ū_i         player's mean residual ratio (actual / median_w1 − 1) over his earlier Week 1s
#       B_i         (σ²/n_i) / (σ²/n_i + τ_p²); σ² pooled within-player variance,
#                   τ_p² = max(0, var(ū_i) − mean(σ²/n_i)); B_i = 1 if σ² can't be estimated
# ---------------------------------------------------------------------------------------------


def lad_ratio(y: np.ndarray, x: np.ndarray) -> float:
    """b minimising Σ|y − b·x| (x > 0): the x-weighted median of y/x."""
    from .calibration import quantile_fit  # local import avoids a circular import
    return float(quantile_fit(x[:, None], y, 0.5)[0])


def _boot_se(y, x, clusters, n_boot, rng) -> float:
    labels, inv = np.unique(clusters, return_inverse=True)
    members = [np.flatnonzero(inv == k) for k in range(len(labels))]
    draws = []
    for _ in range(n_boot):
        idx = np.concatenate([members[k] for k in rng.integers(0, len(labels), len(labels))])
        draws.append(lad_ratio(y[idx], x[idx]))
    return float(np.std(draws, ddof=1))


def fit_week1_position(y, x, pos, clusters, n_boot=200, seed=0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for p in np.unique(pos):
        m = pos == p
        rows.append(dict(position=p, n=int(m.sum()), raw=lad_ratio(y[m], x[m]) - 1,
                         se=_boot_se(y[m], x[m], clusters[m], n_boot, rng)))
    t = pd.DataFrame(rows)
    tau2 = max(0.0, float(np.mean(t["raw"] ** 2) - np.mean(t["se"] ** 2)))
    t["tau2"] = tau2
    t["B"] = t["se"] ** 2 / (t["se"] ** 2 + tau2) if tau2 > 0 else 1.0
    t["gamma"] = (1 - t["B"]) * t["raw"]
    return t


def fit_week1_players(u: np.ndarray, player: np.ndarray, pos: np.ndarray) -> pd.DataFrame:
    """Per player: n, ū, B, shrunk deviation (1 − B)·ū, via normal–normal partial pooling within position."""
    d = pd.DataFrame({"player_id": player, "position": pos, "u": u})
    agg = d.groupby(["player_id", "position"])["u"].agg(n="count", ubar="mean", ss=lambda s: ((s - s.mean()) ** 2).sum())
    agg = agg.reset_index()
    out = []
    for p, a in agg.groupby("position"):
        dof = (a["n"] - 1).sum()
        if dof < 5:  # no repeated openers yet → within-player noise unknown → no player effect
            a = a.assign(sigma2=np.nan, tau2=0.0, B=1.0)
        else:
            sigma2 = a["ss"].sum() / dof
            tau2 = max(0.0, a["ubar"].var(ddof=1) - (sigma2 / a["n"]).mean())
            noise = sigma2 / a["n"]
            a = a.assign(sigma2=sigma2, tau2=tau2, B=noise / (noise + tau2) if tau2 > 0 else 1.0)
        out.append(a)
    res = pd.concat(out, ignore_index=True)
    res["dev"] = (1 - res["B"]) * res["ubar"]
    return res


# First season whose v8m median was itself calibrated (the calibration needs one earlier season).
# Situation effects fitted on the median must start here; 2019 "medians" are uncalibrated means
# (bug found 2026-11-02, see DECISIONS.md). The original v11/v12 runs pass first_season=2019 explicitly.
FIRST_CALIBRATED_SEASON = 2020


def week1_multiplier(df: pd.DataFrame, med_col: str, fit_mask: np.ndarray, player_level: bool = False,
                     first_season: int = FIRST_CALIBRATED_SEASON, n_boot: int = 200) -> tuple[np.ndarray, pd.DataFrame, pd.DataFrame]:
    """Walk-forward Week 1 multiplier (1 for other weeks / no earlier data). Returns (mult, position table, player table)."""
    return situation_multiplier(df, med_col, fit_mask, df["week"].to_numpy() == 1, player_level, first_season, n_boot)


def situation_multiplier(df: pd.DataFrame, med_col: str, fit_mask: np.ndarray, flag: np.ndarray,
                         player_level: bool = False, first_season: int = FIRST_CALIBRATED_SEASON,
                         n_boot: int = 200) -> tuple[np.ndarray, pd.DataFrame, pd.DataFrame]:
    """Same estimator for any pre-game situation flag (Week 1, prime time, ...): rows with flag get
    median × (1 + γ_pos [+ player deviation]); other rows get 1."""
    seasons = df["season"].to_numpy()
    flag = np.asarray(flag, bool)
    pos, pid = df["position"].to_numpy(), df["player_id"].to_numpy()
    x, y = df[med_col].to_numpy(float), df["actual"].to_numpy(float)
    games = df["game_id"].to_numpy()
    ok = fit_mask & flag & np.isfinite(x) & np.isfinite(y) & (x > 0) & (seasons >= first_season)
    mult, ptabs, pltabs = np.ones(len(df)), [], []
    for s in np.unique(seasons):
        train = ok & (seasons < s)
        if train.sum() < 50:
            continue
        t = fit_week1_position(y[train], x[train], pos[train], games[train], n_boot, seed=int(s))
        ptabs.append(t.assign(season=s))
        g_pos = dict(zip(t["position"], t["gamma"]))
        here = np.flatnonzero((seasons == s) & flag)
        gam = np.array([g_pos.get(p, 0.0) for p in pos[here]])
        if player_level:
            base = x[train] * (1 + np.array([g_pos[p] for p in pos[train]]))
            pl = fit_week1_players(y[train] / base - 1, pid[train], pos[train])
            pltabs.append(pl.assign(season=s))
            dev = dict(zip(pl["player_id"], pl["dev"]))
            gam = gam + np.array([dev.get(i, 0.0) for i in pid[here]])
        mult[here] = 1 + gam
    cat = lambda L: pd.concat(L, ignore_index=True) if L else pd.DataFrame()
    return mult, cat(ptabs), cat(pltabs)


PRIME_TIME_START = "19:00"  # US Eastern; fixed in advance (DECISIONS.md, 2026-11-02)


def prime_time_flags(schedules: pd.DataFrame) -> pd.DataFrame:
    """game_id → prime_time (kickoff ≥ 19:00 ET) and slot (Thu / Sun night / Mon / Sat night / other night / day)."""
    s = schedules.loc[schedules["game_type"] == "REG", ["game_id", "weekday", "gametime"]].copy()
    s["prime_time"] = s["gametime"] >= PRIME_TIME_START  # "HH:MM" strings compare correctly
    names = {"Thursday": "Thu night", "Sunday": "Sun night", "Monday": "Mon night", "Saturday": "Sat night"}
    s["slot"] = np.where(s["prime_time"], s["weekday"].map(names).fillna("other night"), "day")
    return s[["game_id", "prime_time", "slot"]]


def placebo_flags(games: pd.DataFrame, flag: np.ndarray, seed: int = 0) -> np.ndarray:
    """Placebo: in each season-week, give the flag to the same NUMBER of games as truly had it, chosen at random."""
    rng = np.random.default_rng(seed)
    gm = pd.DataFrame({"season": games["season"].to_numpy(), "week": games["week"].to_numpy(),
                       "game_id": games["game_id"].to_numpy(), "flag": np.asarray(flag, bool)}).drop_duplicates("game_id")
    fake = set()
    for _, w in gm.groupby(["season", "week"]):
        k = int(w["flag"].sum())
        if k:
            fake.update(rng.choice(w["game_id"].to_numpy(), k, replace=False))
    return games["game_id"].isin(fake).to_numpy()
