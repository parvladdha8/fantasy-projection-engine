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
