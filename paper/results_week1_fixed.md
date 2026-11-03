# Experiment: Week 1 effect on the median (v11 / v11p), BUG-FIX RE-RUN (fitted on seasons ≥ 2020), forward-chained OOS 2020–2023

## Position-level Week 1 effect (fitted on Week 1s of seasons 2020..s−1; γ = % vs the v8m median)

| season | position | n | raw γ | se | τ² | shrinkage B | shrunk γ |
|---|---|---|---|---|---|---|---|
| 2021 | QB | 15 | +9.1% | 12.7% | 0.0133 | 0.55 | +4.1% |
| 2021 | RB | 30 | -4.4% | 11.3% | 0.0133 | 0.49 | -2.3% |
| 2021 | TE | 15 | -34.5% | 18.7% | 0.0133 | 0.73 | -9.5% |
| 2021 | WR | 30 | -5.9% | 12.4% | 0.0133 | 0.54 | -2.7% |
| 2022 | QB | 30 | +8.1% | 11.2% | 0.0013 | 0.90 | +0.8% |
| 2022 | RB | 60 | -7.0% | 6.1% | 0.0013 | 0.73 | -1.9% |
| 2022 | TE | 30 | -22.9% | 16.1% | 0.0013 | 0.95 | -1.1% |
| 2022 | WR | 60 | -2.8% | 13.1% | 0.0013 | 0.93 | -0.2% |
| 2023 | QB | 45 | +8.5% | 7.8% | 0.0000 | 1.00 | +0.0% |
| 2023 | RB | 90 | -7.4% | 5.0% | 0.0000 | 1.00 | -0.0% |
| 2023 | TE | 45 | -14.0% | 9.8% | 0.0000 | 1.00 | -0.0% |
| 2023 | WR | 90 | -0.8% | 12.2% | 0.0000 | 1.00 | -0.0% |

## Player-level deviations (v11p): how much each player's own Week 1 history is trusted

| season | position | players | with ≥ 2 earlier openers | average B | max |deviation| |
|---|---|---|---|---|---|
| 2021 | QB | 15 | 0 | 1.00 | 0.0% |
| 2021 | RB | 30 | 0 | 1.00 | 0.0% |
| 2021 | TE | 15 | 0 | 1.00 | 0.0% |
| 2021 | WR | 30 | 0 | 1.00 | 0.0% |
| 2022 | QB | 20 | 10 | 1.00 | 0.0% |
| 2022 | RB | 42 | 18 | 0.96 | 6.3% |
| 2022 | TE | 19 | 11 | 0.72 | 45.2% |
| 2022 | WR | 39 | 21 | 1.00 | 0.0% |
| 2023 | QB | 22 | 16 | 1.00 | 0.0% |
| 2023 | RB | 48 | 26 | 0.95 | 5.7% |
| 2023 | TE | 23 | 16 | 1.00 | 0.0% |
| 2023 | WR | 50 | 27 | 1.00 | 0.0% |

## Results, Week 1 only (Big-60 = union of all four models' pools; clusters = games)

| pool | A vs B | n | MAE A | MAE B | diff (A−B) | 95% CI | p(A not better) |
|---|---|---|---|---|---|---|---|
| big60 week 1 | v11 vs v8m | 283 | 6.167 | 6.177 | -0.010 | [-0.039, +0.017] | 0.224 |
| big60 week 1 | v11p vs v11 | 283 | 6.220 | 6.167 | +0.054 | [+0.002, +0.133] | 0.981 |
| big60 week 1 | v11p vs v8m | 283 | 6.220 | 6.177 | +0.044 | [-0.017, +0.128] | 0.894 |
| big60 week 1 | v11 vs base | 283 | 6.167 | 6.725 | -0.558 | [-0.884, -0.263] | 0.000 |
| all players week 1 | v11 vs v8m | 1351 | 4.450 | 4.459 | -0.009 | [-0.017, -0.002] | 0.010 |
| all players week 1 | v11p vs v11 | 1351 | 4.460 | 4.450 | +0.010 | [-0.001, +0.027] | 0.958 |
| all players week 1 | v11p vs v8m | 1351 | 4.460 | 4.459 | +0.001 | [-0.013, +0.019] | 0.508 |
| all players week 1 | v11 vs base | 1351 | 4.450 | 4.670 | -0.221 | [-0.327, -0.129] | 0.000 |
| big60 week 1, 2021–23 only (descriptive) | v11 vs v8m | 209 | 6.324 | 6.337 | -0.014 | [-0.051, +0.022] | 0.236 |
| big60 week 1, 2021–23 only (descriptive) | v11p vs v11 | 209 | 6.396 | 6.324 | +0.073 | [+0.003, +0.177] | 0.980 |
| big60 week 1, 2021–23 only (descriptive) | v11p vs v8m | 209 | 6.396 | 6.337 | +0.059 | [-0.023, +0.170] | 0.908 |
| big60 week 1, 2021–23 only (descriptive) | v11 vs base | 209 | 6.324 | 6.733 | -0.410 | [-0.743, -0.090] | 0.006 |

## Diagnostics: is Week 1 different for v8m? (Big-60; descriptive)

| position | Week 1 n | Week 1 median error (proj − actual) | Week 1 share scoring above median | weeks 2+ share above median | Week 1 floor–ceiling coverage | weeks 2+ coverage |
|---|---|---|---|---|---|---|
| QB | 47 | +0.97 | 44.7% | 48.6% | 76.6% | 81.3% |
| RB | 92 | +1.25 | 41.3% | 52.8% | 81.5% | 80.1% |
| WR | 97 | +0.65 | 46.4% | 50.3% | 85.6% | 84.2% |
| TE | 47 | +2.10 | 34.0% | 52.4% | 85.1% | 84.8% |
| all | 283 | +1.25 | 42.4% | 51.2% | 82.7% | 82.5% |

## Big-60 Week 1 MAE by position (descriptive)

| model | QB | RB | WR | TE |
|---|---|---|---|---|
| base | 7.079 | 6.510 | 7.285 | 5.637 |
| v8m | 6.556 | 5.894 | 6.695 | 5.283 |
| v11 | 6.540 | 5.880 | 6.706 | 5.242 |
| v11p | 6.540 | 5.917 | 6.706 | 5.493 |
