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
