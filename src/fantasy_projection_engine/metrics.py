"""Error metrics.

MAE  = average size of the miss, in fantasy points. Primary metric.
RMSE = like MAE but squares misses first, so big misses count extra.
"""

import numpy as np


def mae(actual, predicted) -> float:
    a, p = np.asarray(actual, float), np.asarray(predicted, float)
    return float(np.mean(np.abs(a - p)))


def rmse(actual, predicted) -> float:
    a, p = np.asarray(actual, float), np.asarray(predicted, float)
    return float(np.sqrt(np.mean((a - p) ** 2)))


def paired_bootstrap(err_a, err_b, clusters, n_boot: int = 2000, seed: int = 0) -> dict:
    """Is model A's MAE really lower than model B's? (rigor rule 6)

    err_a, err_b: absolute errors of A and B on the SAME player-games (paired).
    clusters: group label per row (e.g. season-week). We resample whole clusters,
    because errors in the same week are correlated (weather, scoring environment),
    so treating every row as independent would overstate our certainty.

    Returns the mean difference (A − B; negative = A better), a 95% interval,
    and the share of bootstrap draws where A was NOT better (a one-sided p-value).
    """
    d = np.asarray(err_a, float) - np.asarray(err_b, float)
    labels, idx = np.unique(np.asarray(clusters), return_inverse=True)
    sums = np.bincount(idx, weights=d)
    counts = np.bincount(idx)
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, len(labels), size=(n_boot, len(labels)))
    boot = sums[draws].sum(1) / counts[draws].sum(1)
    return {
        "diff": float(d.mean()),
        "ci_low": float(np.percentile(boot, 2.5)),
        "ci_high": float(np.percentile(boot, 97.5)),
        "p_a_not_better": float((boot >= 0).mean()),
    }
