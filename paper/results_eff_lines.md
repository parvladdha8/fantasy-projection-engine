# Betting lines for efficiency (v5), forward-chained OOS 2020–2023

v5 = v4 with points-per-opportunity × (1 + α + β·(implied − ī)), fitted walk-forward by season.
v5-cal = α only (control: calibration without betting information). Headline (pre-registered): v5 vs v5-cal.
Copied from `reports/exp_eff_lines.md`; regenerate with `uv run python scripts/exp_eff_lines.py`.

## Settings per fold (hl_vol/hl_eff/k/hl_long/m/hl_team)

| season | model | rec | rush | pass |
|---|---|---|---|---|
| 2020 | v4 (= v5 settings) | 4/64/200/8/4/8 | 2/6/100/–/0/4 | 4/6/200/–/0/64 |
| 2021 | v4 (= v5 settings) | 4/64/100/16/4/32 | 1/8/50/8/2/8 | 4/8/100/64/4/64 |
| 2022 | v4 (= v5 settings) | 3/64/100/16/8/64 | 1/8/50/8/2/8 | 1/8/100/64/2/32 |
| 2023 | v4 (= v5 settings) | 3/64/100/32/8/16 | 1/6/50/8/4/8 | 4/8/200/64/2/16 |

## Fitted environment effect (coefficients from seasons < s)

| season | component | β: change in points/opportunity per +1 implied point | mean multiplier (1 + α) |
|---|---|---|---|
| 2020 | rec | +1.33% | 0.987 |
| 2020 | rush | +1.25% | 1.035 |
| 2020 | pass | +1.90% | 0.954 |
| 2021 | rec | +1.25% | 0.971 |
| 2021 | rush | +1.21% | 1.011 |
| 2021 | pass | +1.54% | 0.937 |
| 2022 | rec | +1.15% | 0.952 |
| 2022 | rush | +1.25% | 0.983 |
| 2022 | pass | +1.33% | 0.920 |
| 2023 | rec | +1.11% | 0.947 |
| 2023 | rush | +1.22% | 0.979 |
| 2023 | pass | +1.73% | 0.909 |

## Results (Big-60 = union of all four models' pools)

| pool | A vs B | n | MAE A | MAE B | diff (A−B) | 95% CI | p(A not better) |
|---|---|---|---|---|---|---|---|
| big60 | v5 vs v5cal | 5029 | 6.477 | 6.529 | -0.052 | [-0.071, -0.033] | 0.000 |
| big60 | v5 vs v4 | 5029 | 6.477 | 6.550 | -0.072 | [-0.095, -0.051] | 0.000 |
| big60 | v5cal vs v4 | 5029 | 6.529 | 6.550 | -0.021 | [-0.037, -0.006] | 0.003 |
| big60 | v5 vs base | 5029 | 6.477 | 6.666 | -0.188 | [-0.242, -0.138] | 0.000 |
| all | v5 vs v5cal | 25788 | 4.279 | 4.302 | -0.023 | [-0.030, -0.016] | 0.000 |
| all | v5 vs v4 | 25788 | 4.279 | 4.326 | -0.047 | [-0.056, -0.039] | 0.000 |
| all | v5cal vs v4 | 25788 | 4.302 | 4.326 | -0.024 | [-0.028, -0.019] | 0.000 |
| all | v5 vs base | 25788 | 4.279 | 4.348 | -0.069 | [-0.087, -0.051] | 0.000 |

## Big-60 MAE by position (descriptive)

| model | QB | RB | WR | TE |
|---|---|---|---|---|
| base | 6.587 | 6.767 | 7.142 | 5.611 |
| v4 | 6.403 | 6.666 | 7.010 | 5.567 |
| v5cal | 6.428 | 6.658 | 6.963 | 5.529 |
| v5 | 6.341 | 6.617 | 6.919 | 5.479 |

## Bias in Big-60 pool

| base | v4 | v5cal | v5 |
|---|---|---|---|
| +0.81 | +0.30 | -0.03 | +0.08 |