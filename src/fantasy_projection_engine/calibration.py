"""Loss alignment: map the model's MEAN projection to the MEDIAN outcome (v8).

The Big-60 grades MAE, which is minimised by the median; fantasy points are right-skewed,
so the mean is systematically too high for MAE. Final step, per position:

    median_proj = a_pos + b_pos · proj        fitted by least absolute deviations (τ = 0.5)

Walk-forward: season s uses fit rows from seasons first_season..s−1 only.
method="ols" fits the same map by least squares (control: recalibration without loss alignment).
method="lad_mult" drops the intercept: median_proj = b_pos · proj (v8m; 0 stays 0, no lift for fringe players).
"""

import numpy as np
import pandas as pd


def quantile_fit(X: np.ndarray, y: np.ndarray, tau: float = 0.5, iters: int = 200, tol: float = 1e-9) -> np.ndarray:
    """Linear quantile regression by iteratively reweighted least squares.

    Minimises Σ ρ_τ(y − Xb), ρ_τ(r) = r·(τ − 1[r<0]); τ = 0.5 gives least absolute deviations.
    Each step solves weighted least squares with weights |τ − 1[r<0]| / max(|r|, ε).
    """
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    eps = 1e-6 * max(1.0, np.abs(y).mean())
    for _ in range(iters):
        r = y - X @ b
        w = np.where(r < 0, 1 - tau, tau) / np.maximum(np.abs(r), eps)
        sw = np.sqrt(w)
        b_new = np.linalg.lstsq(X * sw[:, None], y * sw, rcond=None)[0]
        if np.max(np.abs(b_new - b)) < tol:
            return b_new
        b = b_new
    return b


def median_calibration(df: pd.DataFrame, proj_col: str, fit_mask: np.ndarray, method: str = "lad",
                       first_season: int = 2019, tau: float = 0.5) -> tuple[np.ndarray, pd.DataFrame]:
    """Walk-forward per-position map proj → a + b·proj. Returns calibrated projections and a coefficient table."""
    seasons, pos = df["season"].to_numpy(), df["position"].to_numpy()
    x, y = df[proj_col].to_numpy(float), df["actual"].to_numpy(float)
    ok = fit_mask & np.isfinite(x) & np.isfinite(y) & (seasons >= first_season)
    out, rows = x.copy(), []
    for s in np.unique(seasons):
        for p in np.unique(pos):
            train = ok & (seasons < s) & (pos == p)
            if train.sum() < 50:
                continue
            if method == "lad_mult":
                a, b = 0.0, quantile_fit(x[train, None], y[train], tau)[0]
            else:
                X = np.column_stack([np.ones(train.sum()), x[train]])
                a, b = quantile_fit(X, y[train], tau) if method == "lad" else np.linalg.lstsq(X, y[train], rcond=None)[0]
            here = (seasons == s) & (pos == p)
            out[here] = a + b * x[here]
            rows.append(dict(season=int(s), position=p, a=a, b=b, n=int(train.sum())))
    return out, pd.DataFrame(rows)


def shrunk_volatility(g: pd.DataFrame, window: int = 16, prior: float = 8, min_games: int = 2) -> pd.Series:
    """Player's pre-game volatility (coefficient of variation of his previous ≤ `window` games), shrunk
    toward the position's average CV:  cv_shr = (n·cv + prior·cv_pos) / (n + prior),  minus cv_pos (centred).

    cv_pos = average CV over all EARLIER seasons' player-games at that position (walk-forward).
    Rows must be sorted by player then time. Returns z (0 when < min_games of history).
    """
    past = g.groupby("player_id")["actual"].shift(1)
    roll = past.groupby(g["player_id"]).rolling(window, min_periods=min_games)
    sd = roll.std().reset_index(level=0, drop=True).reindex(g.index)
    mu = roll.mean().reset_index(level=0, drop=True).reindex(g.index)
    n = past.notna().groupby(g["player_id"]).cumsum().clip(upper=window)
    cv = (sd / mu.where(mu > 1)).clip(upper=5)
    # position average CV from earlier seasons only
    by = pd.DataFrame({"position": g["position"], "season": g["season"], "cv": cv}).dropna()
    season_mean = by.groupby(["position", "season"])["cv"].agg(["sum", "count"]).sort_index()
    cum = season_mean.groupby(level="position").cumsum().groupby(level="position").shift(1)
    cv_pos_tab = (cum["sum"] / cum["count"]).rename("cv_pos")
    cv_pos = pd.Series(cv_pos_tab.reindex(pd.MultiIndex.from_arrays([g["position"], g["season"]])).to_numpy(), index=g.index)
    z = (n * cv + prior * cv_pos) / (n + prior) - cv_pos
    return z.fillna(0.0)


def quantile_band(df: pd.DataFrame, proj_col: str, z_col: str | None, fit_mask: np.ndarray, tau: float,
                  first_season: int = 2019) -> tuple[np.ndarray, pd.DataFrame]:
    """Walk-forward per-position quantile regression  q_τ = a + b·proj (+ c·proj·z)."""
    seasons, pos = df["season"].to_numpy(), df["position"].to_numpy()
    x, y = df[proj_col].to_numpy(float), df["actual"].to_numpy(float)
    z = df[z_col].to_numpy(float) if z_col else np.zeros(len(df))
    ok = fit_mask & np.isfinite(x) & np.isfinite(y) & np.isfinite(z) & (seasons >= first_season)
    cols = lambda m: np.column_stack([np.ones(m.sum()), x[m]] + ([x[m] * z[m]] if z_col else []))
    out, rows = np.full(len(df), np.nan), []
    for s in np.unique(seasons):
        for p in np.unique(pos):
            train = ok & (seasons < s) & (pos == p)
            if train.sum() < 50:
                continue
            b = quantile_fit(cols(train), y[train], tau)
            here = (seasons == s) & (pos == p) & np.isfinite(x)
            out[here] = cols(here) @ b
            rows.append(dict(season=int(s), position=p, tau=tau, a=b[0], b=b[1], c=b[2] if z_col else 0.0))
    return out, pd.DataFrame(rows)
