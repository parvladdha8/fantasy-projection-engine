# Experiment: floor / median / ceiling, simple version (v9), forward-chained OOS 2020–2023

## Fitted percentages of the mean projection (from seasons 2019..s−1)

| season | position | floor (10th) | median (50th) | ceiling (90th) |
|---|---|---|---|---|
| 2020 | QB | 48% | 102% | 159% |
| 2020 | RB | 35% | 85% | 167% |
| 2020 | TE | 25% | 92% | 203% |
| 2020 | WR | 31% | 93% | 188% |
| 2021 | QB | 51% | 104% | 165% |
| 2021 | RB | 32% | 87% | 172% |
| 2021 | TE | 25% | 91% | 180% |
| 2021 | WR | 31% | 96% | 185% |
| 2022 | QB | 48% | 102% | 165% |
| 2022 | RB | 30% | 87% | 172% |
| 2022 | TE | 26% | 92% | 190% |
| 2022 | WR | 32% | 93% | 183% |
| 2023 | QB | 49% | 101% | 160% |
| 2023 | RB | 31% | 87% | 172% |
| 2023 | TE | 25% | 92% | 188% |
| 2023 | WR | 32% | 92% | 182% |

## Calibration (target: 80% inside, 10% below, 10% above)

| pool | n | inside | below floor | above ceiling |
|---|---|---|---|---|
| **Big-60, v9** | 4903 | 80.8% | 9.6% | 9.5% |
| Big-60, benchmark (baseline-centred) | 4903 | 81.0% | 8.9% | 10.2% |
| All players, v9 | 25788 | 51.4% | 32.0% | 16.6% |
| Big-60 QB, v9 | 819 | 81.4% | 9.3% | 9.3% |
| Big-60 RB, v9 | 1574 | 79.4% | 10.3% | 10.4% |
| Big-60 WR, v9 | 1667 | 82.0% | 9.2% | 8.8% |
| Big-60 TE, v9 | 843 | 80.7% | 9.7% | 9.6% |
| Big-60 steady (low CV), v9 | 1586 | 81.4% | 9.8% | 8.8% |
| Big-60 middle, v9 | 1585 | 83.4% | 8.1% | 8.5% |
| Big-60 volatile (high CV), v9 | 1586 | 78.2% | 10.7% | 11.0% |
| Big-60 no volatility history (< 6 games) | 146 | 74.7% | 13.0% | 12.3% |

## Interval score (lower = better; paired, week-clustered bootstrap)

| pool | n | v9 | benchmark | diff | 95% CI | p(v9 not better) |
|---|---|---|---|---|---|---|
| big60 | 4903 | 28.515 | 28.946 | -0.431 | [-0.659, -0.211] | 0.000 |
| all | 25788 | 20.987 | 21.395 | -0.408 | [-0.522, -0.298] | 0.000 |

## Average interval width, Big-60 (points)

| model | floor | median | ceiling | width |
|---|---|---|---|---|
| v9 | 5.2 | 14.1 | 26.7 | 21.5 |
| benchmark | 5.0 | 13.7 | 26.3 | 21.4 |