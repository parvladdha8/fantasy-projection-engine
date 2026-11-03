# Experiment: prime-time effect on the median (v12 / v12p / placebo), forward-chained OOS 2020–2023

Prime-time games (kickoff ≥ 19:00 ET) in 2020–23: 220 of 1071. Big-60 prime-time player-games: 1125 of 5043.

## Position-level prime-time effect (fitted on prime-time games of seasons 2019..s−1; γ = % vs v8m median)

| season | position | n | raw γ | se | shrinkage B | shrunk γ | placebo shrunk γ |
|---|---|---|---|---|---|---|---|
| 2020 | QB | 59 | +1.1% | 8.8% | 0.49 | +0.6% | -5.9% |
| 2020 | RB | 115 | -15.8% | 7.0% | 0.38 | -9.9% | -18.5% |
| 2020 | TE | 57 | -10.7% | 6.5% | 0.34 | -7.0% | -2.4% |
| 2020 | WR | 107 | -13.4% | 7.5% | 0.41 | -7.9% | -9.9% |
| 2021 | QB | 117 | +0.0% | 5.8% | 0.42 | +0.0% | -1.2% |
| 2021 | RB | 217 | -14.1% | 5.5% | 0.39 | -8.6% | -2.4% |
| 2021 | TE | 117 | -7.4% | 6.7% | 0.49 | -3.8% | -0.2% |
| 2021 | WR | 213 | -8.4% | 5.0% | 0.34 | -5.5% | -1.5% |
| 2022 | QB | 179 | -1.7% | 4.9% | 0.36 | -1.1% | -4.4% |
| 2022 | RB | 333 | -13.7% | 4.1% | 0.29 | -9.8% | -7.5% |
| 2022 | TE | 175 | -0.5% | 5.5% | 0.42 | -0.3% | -4.5% |
| 2022 | WR | 339 | -8.0% | 4.2% | 0.29 | -5.7% | -7.7% |
| 2023 | QB | 245 | -3.3% | 3.8% | 0.51 | -1.6% | -1.3% |
| 2023 | RB | 447 | -9.3% | 4.4% | 0.58 | -3.9% | -2.8% |
| 2023 | TE | 227 | +0.3% | 5.9% | 0.71 | +0.1% | -0.1% |
| 2023 | WR | 455 | -6.4% | 3.8% | 0.51 | -3.1% | -1.8% |

## Player-level prime-time splits (v12p): how much each player's own prime-time history is trusted

| season | position | players | with ≥ 2 earlier prime-time games | average B | max |deviation| |
|---|---|---|---|---|---|
| 2020 | QB | 21 | 15 | 0.87 | 7.0% |
| 2020 | RB | 43 | 27 | 1.00 | 0.0% |
| 2020 | TE | 24 | 13 | 0.97 | 3.4% |
| 2020 | WR | 41 | 23 | 0.77 | 19.9% |
| 2021 | QB | 26 | 22 | 0.51 | 22.7% |
| 2021 | RB | 59 | 40 | 0.46 | 97.7% |
| 2021 | TE | 34 | 26 | 0.72 | 32.0% |
| 2021 | WR | 59 | 44 | 1.00 | 0.0% |
| 2022 | QB | 31 | 25 | 0.97 | 1.5% |
| 2022 | RB | 77 | 59 | 0.80 | 24.9% |
| 2022 | TE | 39 | 31 | 0.94 | 6.7% |
| 2022 | WR | 64 | 54 | 0.94 | 6.9% |
| 2023 | QB | 34 | 29 | 1.00 | 0.0% |
| 2023 | RB | 86 | 62 | 1.00 | 0.0% |
| 2023 | TE | 39 | 33 | 0.74 | 24.8% |
| 2023 | WR | 78 | 63 | 1.00 | 0.0% |

## Results (Big-60 = union of all five models' pools; week-clustered)

| pool | A vs B | n | MAE A | MAE B | diff (A−B) | 95% CI | p(A not better) |
|---|---|---|---|---|---|---|---|
| **big60 prime time (headline)** | v12 vs v8m | 1125 | 6.442 | 6.414 | +0.028 | [-0.022, +0.082] | 0.854 |
| big60 placebo-labelled games | v12placebo vs v8m | 1040 | 6.403 | 6.318 | +0.085 | [+0.012, +0.162] | 0.991 |
| big60 prime time | v12p vs v12 | 1125 | 6.463 | 6.442 | +0.021 | [-0.054, +0.094] | 0.699 |
| big60 prime time | v12p vs v8m | 1125 | 6.463 | 6.414 | +0.049 | [-0.034, +0.130] | 0.878 |
| all players prime time | v12 vs v8m | 5294 | 4.110 | 4.133 | -0.023 | [-0.036, -0.009] | 0.001 |
| big60 full season | v12 vs v8m | 5043 | 6.431 | 6.424 | +0.006 | [-0.005, +0.018] | 0.854 |
| big60 full season | v12 vs v12placebo | 5043 | 6.431 | 6.442 | -0.011 | [-0.026, +0.002] | 0.057 |
| big60 full season | v8m vs base | 5043 | 6.424 | 6.669 | -0.245 | [-0.318, -0.170] | 0.000 |

## Diagnostics: is prime time different for v8m? (Big-60; descriptive)

| group | n | median error (proj − actual) | share above median | floor–ceiling coverage |
|---|---|---|---|---|
| not prime time | 3918 | -0.22 | 50.8% | 82.3% |
| prime time, QB | 214 | +1.29 | 44.4% | 82.2% |
| prime time, RB | 355 | -0.14 | 51.3% | 79.4% |
| prime time, WR | 371 | +0.17 | 49.6% | 86.8% |
| prime time, TE | 185 | -0.59 | 56.2% | 80.5% |
| prime time, all | 1125 | -0.06 | 50.2% | 82.6% |
| slot: Mon night | 359 | -0.02 | 50.1% | 81.3% |
| slot: Sat night | 67 | -0.73 | 53.7% | 79.1% |
| slot: Sun night | 395 | +1.07 | 45.6% | 84.3% |
| slot: Thu night | 285 | -0.68 | 54.7% | 83.2% |
| slot: other night | 19 | -4.39 | 68.4% | 73.7% |

## Big-60 prime-time MAE by position (descriptive)

| model | QB | RB | WR | TE |
|---|---|---|---|---|
| base | 6.618 | 6.797 | 6.978 | 6.120 |
| v8m | 6.377 | 6.419 | 6.667 | 5.939 |
| v12 | 6.352 | 6.482 | 6.678 | 5.992 |
| v12p | 6.301 | 6.569 | 6.678 | 6.013 |
| v12placebo | 6.380 | 6.453 | 6.667 | 5.944 |
