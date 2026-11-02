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
