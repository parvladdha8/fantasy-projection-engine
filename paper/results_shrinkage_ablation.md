# Shrinkage ablation: opportunity × efficiency vs baseline

Out-of-sample, forward-chained, seasons 2020–2023 (tuned on 2019..s−1). Big-60 pool n = 4,867 player-games; all-players n = 25,788.

## Main table

| Model | All-players MAE | Big-60 MAE | Big-60 Δ vs baseline | 95% CI | p (not better) | Big-60 RMSE | Big-60 Spearman | Big-60 bias |
|---|---|---|---|---|---|---|---|---|
| Baseline: trailing weighted average of PPR points | 4.348 | 6.648 | — | — | — | 8.385 | 0.362 | +0.94 |
| Opp × Eff, no shrinkage (k = 0, m = 0) | 4.365 | 6.651 | +0.003 | [-0.025, +0.031] | 0.610 | 8.382 | 0.365 | +0.98 |
| Opp × Eff, efficiency shrinkage only (pre-volume-shrinkage, v1) | 4.375 | 6.597 | -0.051 | [-0.092, -0.010] | 0.006 | 8.334 | 0.361 | +0.58 |
| Opp × Eff, efficiency + volume shrinkage (current, v2) | 4.360 | 6.587 | -0.062 | [-0.103, -0.019] | 0.003 | 8.324 | 0.362 | +0.53 |

## Step-by-step contribution on the Big-60 (each row vs the row above)

| Step | Δ MAE | 95% CI | p (not better) |
|---|---|---|---|
| Split into opportunity × efficiency (no shrinkage) | +0.003 | [-0.025, +0.031] | 0.610 |
| + efficiency shrinkage (empirical Bayes, k) | -0.054 | [-0.088, -0.022] | 0.000 |
| + volume shrinkage (m) | -0.011 | [-0.020, -0.001] | 0.013 |

## Big-60 MAE by position

| Model | QB | RB | WR | TE |
|---|---|---|---|---|
| Baseline: trailing weighted average of PPR points | 6.589 | 6.688 | 7.177 | 5.587 |
| Opp × Eff, no shrinkage (k = 0, m = 0) | 6.565 | 6.753 | 7.141 | 5.577 |
| Opp × Eff, efficiency shrinkage only (pre-volume-shrinkage, v1) | 6.502 | 6.675 | 7.090 | 5.571 |
| Opp × Eff, efficiency + volume shrinkage (current, v2) | 6.511 | 6.664 | 7.076 | 5.547 |

## Notes

- Δ < 0 means lower error than the comparison model. CI = 95% paired bootstrap resampling whole season-weeks.
- Bias = mean(projection − actual); positive = over-projection.
- All model settings are re-tuned inside each fold on earlier seasons only; 2024 and 2025 are untouched.
- Numbers differ slightly from earlier experiment reports because the Big-60 union pool here includes all four models.
- Per-position values are descriptive; they are not individually significance-tested (multiple comparisons).