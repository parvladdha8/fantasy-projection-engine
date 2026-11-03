# Experiment: opponent strength by position (v14 + shuffled-opponent placebo), forward-chained OOS 2020–2023

Defense effect = how much the players it faced beat their own v8m median, relative to the league ratio, decayed (half-life 8 defense-games), EB-shrunk per position. Hyperparameters from seasons 2020..s−1.

## Hyperparameters per fold

| season | position | league ratio R (mean/median) | σ² (per expected pt) | τ² | true spread of defenses (sd = √τ²) | placebo τ² | defense-seasons |
|---|---|---|---|---|---|---|---|
| 2021 | QB | 1.037 | 3.282 | 0.0020 | 4.5% | 0.0000 | 32 |
| 2021 | RB | 1.110 | 5.241 | 0.0102 | 10.1% | 0.0000 | 32 |
| 2021 | TE | 1.037 | 4.090 | 0.0338 | 18.4% | 0.0000 | 32 |
| 2021 | WR | 1.113 | 5.189 | 0.0095 | 9.7% | 0.0000 | 32 |
| 2022 | QB | 1.000 | 3.460 | 0.0000 | 0.0% | 0.0000 | 64 |
| 2022 | RB | 1.093 | 5.323 | 0.0057 | 7.5% | 0.0000 | 64 |
| 2022 | TE | 1.076 | 4.677 | 0.0403 | 20.1% | 0.0000 | 64 |
| 2022 | WR | 1.071 | 5.014 | 0.0043 | 6.5% | 0.0008 | 64 |
| 2023 | QB | 0.999 | 3.383 | 0.0000 | 0.0% | 0.0000 | 96 |
| 2023 | RB | 1.096 | 5.302 | 0.0051 | 7.1% | 0.0000 | 96 |
| 2023 | TE | 1.073 | 4.860 | 0.0383 | 19.6% | 0.0000 | 96 |
| 2023 | WR | 1.079 | 5.120 | 0.0026 | 5.1% | 0.0000 | 96 |

## Shrunk effects δ applied (all rows, 2021–23)

| position | average shrinkage B | δ 10th pct | δ median | δ 90th pct | max |δ| |
|---|---|---|---|---|---|
| QB | 0.96 | -1.2% | +0.0% | +0.4% | 4.4% |
| RB | 0.70 | -5.8% | -0.1% | +5.4% | 13.7% |
| WR | 0.72 | -5.2% | -0.3% | +3.8% | 13.6% |
| TE | 0.43 | -13.9% | -0.0% | +15.3% | 48.6% |

## Results (Big-60 = union of all four models' pools; all weeks; week-clustered; headline 2021–23)

| pool | A vs B | n | MAE A | MAE B | diff (A−B) | 95% CI | p(A not better) |
|---|---|---|---|---|---|---|---|
| **big60 (headline)** | v14 vs v8m | 3853 | 6.375 | 6.375 | -0.000 | [-0.021, +0.020] | 0.485 |
| big60 | v14placebo vs v8m | 3853 | 6.376 | 6.375 | +0.001 | [-0.000, +0.002] | 0.858 |
| big60 | v14 vs v14placebo | 3853 | 6.375 | 6.376 | -0.001 | [-0.022, +0.020] | 0.464 |
| all players | v14 vs v8m | 19635 | 4.156 | 4.157 | -0.001 | [-0.007, +0.005] | 0.358 |
| big60 2020–23 (descriptive) | v14 vs v8m | 5051 | 6.413 | 6.413 | -0.000 | [-0.016, +0.015] | 0.503 |
| big60 | v8m vs base | 3853 | 6.375 | 6.602 | -0.227 | [-0.307, -0.141] | 0.000 |
| big60 QB (descriptive) | v14 vs v8m | 624 | 6.292 | 6.293 | -0.001 | [-0.012, +0.010] | 0.408 |
| big60 RB (descriptive) | v14 vs v8m | 1234 | 6.456 | 6.471 | -0.015 | [-0.045, +0.014] | 0.162 |
| big60 WR (descriptive) | v14 vs v8m | 1302 | 6.819 | 6.829 | -0.010 | [-0.047, +0.027] | 0.286 |
| big60 TE (descriptive) | v14 vs v8m | 693 | 5.474 | 5.427 | +0.047 | [-0.044, +0.133] | 0.849 |

## Stickiness: does a defense's first-half deviation predict its second half? (2020–23, descriptive)

| position | correlation (real opponents) | correlation (placebo opponents) | defense-seasons |
|---|---|---|---|
| QB | +0.04 | -0.06 | 192 |
| RB | +0.07 | +0.01 | 192 |
| WR | +0.07 | +0.05 | 192 |
| TE | +0.06 | -0.06 | 191 |
