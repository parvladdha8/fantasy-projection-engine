# Experiment: bad-weather effect on the median (v13 + two placebos), forward-chained OOS 2020–2023

Bad weather = outdoor/open roof AND (wind ≥ 15 mph OR temp ≤ 32°F). Missing weather → not flagged.

## Weather data by season (regular season)

| season | games | outdoor/open | outdoor with missing weather | bad weather | wind only | cold only | both |
|---|---|---|---|---|---|---|---|
| 2019 | 256 | 197 | 7 | 28 | 22 | 6 | 0 |
| 2020 | 256 | 165 | 0 | 28 | 25 | 2 | 1 |
| 2021 | 272 | 193 | 11 | 37 | 29 | 8 | 0 |
| 2022 | 271 | 187 | 91 | 25 | 9 | 12 | 4 |
| 2023 | 272 | 191 | 41 | 16 | 12 | 4 | 0 |

## Position-level bad-weather effect (fitted on bad-weather games of seasons 2020..s−1; γ = % vs v8m median)

| season | position | n | raw γ | se | shrinkage B | shrunk γ | placebo (any game) γ | placebo (outdoor) γ |
|---|---|---|---|---|---|---|---|---|
| 2021 | QB | 31 | +8.8% | 13.0% | 1.00 | +0.0% | +1.8% | -0.0% |
| 2021 | RB | 59 | -5.4% | 9.9% | 1.00 | -0.0% | -15.8% | -0.0% |
| 2021 | TE | 27 | -19.6% | 22.7% | 1.00 | -0.0% | -6.5% | -0.0% |
| 2021 | WR | 62 | -1.7% | 10.7% | 1.00 | -0.0% | -5.2% | -0.0% |
| 2022 | QB | 67 | -10.9% | 5.5% | 0.39 | -6.6% | -0.0% | -0.0% |
| 2022 | RB | 137 | -8.4% | 6.2% | 0.46 | -4.6% | -0.0% | -0.0% |
| 2022 | TE | 63 | -6.0% | 10.9% | 0.72 | -1.7% | +0.0% | +0.0% |
| 2022 | WR | 133 | -13.1% | 5.1% | 0.36 | -8.4% | -0.0% | -0.0% |
| 2023 | QB | 96 | -4.1% | 6.6% | 0.51 | -2.0% | -0.3% | -0.0% |
| 2023 | RB | 189 | -7.4% | 5.1% | 0.39 | -4.5% | -3.6% | -0.0% |
| 2023 | TE | 86 | -5.7% | 8.2% | 0.61 | -2.2% | +0.1% | +0.0% |
| 2023 | WR | 172 | -15.0% | 4.7% | 0.35 | -9.8% | -1.4% | -0.0% |

## Results (Big-60 = union of all five models' pools; week-clustered; headline seasons 2021–2023)

| pool | A vs B | n | MAE A | MAE B | diff (A−B) | 95% CI | p(A not better) |
|---|---|---|---|---|---|---|---|
| **big60 bad weather (headline)** | v13 vs v8m | 345 | 5.970 | 5.931 | +0.039 | [-0.035, +0.118] | 0.836 |
| big60 placebo-labelled games (any game) | v13any vs v8m | 361 | 6.105 | 6.036 | +0.070 | [-0.021, +0.167] | 0.935 |
| big60 placebo-labelled games (outdoor) | v13out vs v8m | 358 | 6.209 | 6.209 | +0.000 | [+0.000, +0.000] | 1.000 |
| all players bad weather | v13 vs v8m | 1890 | 3.925 | 3.929 | -0.004 | [-0.019, +0.014] | 0.334 |
| big60 full season | v13 vs v8m | 3742 | 6.391 | 6.388 | +0.004 | [-0.003, +0.011] | 0.856 |
| big60 full season | v13 vs v13any | 3742 | 6.391 | 6.394 | -0.003 | [-0.015, +0.009] | 0.329 |
| big60 full season | v13 vs v13out | 3742 | 6.391 | 6.388 | +0.004 | [-0.003, +0.011] | 0.856 |
| big60 bad weather, 2020–23 (descriptive) | v13 vs v8m | 494 | 6.171 | 6.144 | +0.028 | [-0.025, +0.086] | 0.859 |

## Diagnostics: is bad weather different for v8m? (Big-60, OOS 2020–23; descriptive)

| group | n | median error (proj − actual) | share above median | floor–ceiling coverage |
|---|---|---|---|---|
| dome/closed | 1647 | -0.89 | 55.1% | 82.0% |
| outdoor, fine | 2799 | +0.25 | 48.9% | 82.9% |
| bad weather, QB | 83 | +0.86 | 47.0% | 78.3% |
| bad weather, RB | 169 | +0.96 | 46.2% | 78.7% |
| bad weather, WR | 159 | +1.77 | 41.5% | 86.2% |
| bad weather, TE | 83 | +0.26 | 48.2% | 83.1% |
| bad weather, all | 494 | +0.97 | 45.1% | 81.8% |
| cause: wind only | 358 | +1.17 | 44.7% | 83.0% |
| cause: cold only | 105 | +0.88 | 45.7% | 78.1% |
| cause: wind + cold | 31 | +0.19 | 48.4% | 80.6% |
| outdoor, weather missing | 629 | +0.58 | 46.9% | 84.4% |

## Big-60 bad-weather MAE by position (2021–23; descriptive)

| model | QB | RB | WR | TE |
|---|---|---|---|---|
| base | 6.659 | 6.930 | 6.848 | 4.940 |
| v8m | 6.592 | 6.205 | 6.233 | 4.149 |
| v13 | 6.774 | 6.172 | 6.296 | 4.140 |
| v13any | 6.610 | 6.155 | 6.234 | 4.151 |
| v13out | 6.592 | 6.205 | 6.233 | 4.149 |
