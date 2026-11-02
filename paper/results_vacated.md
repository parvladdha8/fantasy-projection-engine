# Experiment: vacated opportunity from injured teammates (v7), forward-chained OOS 2020–2023

Absences (Out/Doubtful, skill positions, dev seasons): 1,802; linked to a prior game for the same team: 1,702. Big-60 player-games with an absent teammate (V > 0): 2,075 of 5,012 (41%).

## v5 settings per fold (hl_vol/hl_eff/k/hl_long/m/hl_team)

| season | rec | rush | pass |
|---|---|---|---|
| 2020 | 4/64/200/8/4/8 | 2/6/100/–/0/4 | 4/6/200/–/0/64 |
| 2021 | 4/64/100/16/4/32 | 1/8/50/8/2/8 | 4/8/100/64/4/64 |
| 2022 | 3/64/100/16/8/64 | 1/8/50/8/2/8 | 1/8/100/64/2/32 |
| 2023 | 3/64/100/32/8/16 | 1/6/50/8/4/8 | 4/8/200/64/2/16 |

## Fitted λ (from seasons < s): % growth in share per unit of vacated share

| season | model | component | λ same position | λ other positions |
|---|---|---|---|---|
| 2020 | v7 | rec | +0.60 | -0.17 |
| 2020 | v7 | rush | +0.25 | -0.22 |
| 2020 | v7placebo | rec | -0.10 | -0.33 |
| 2020 | v7placebo | rush | -0.07 | -0.12 |
| 2021 | v7 | rec | +0.55 | -0.16 |
| 2021 | v7 | rush | +0.35 | -0.02 |
| 2021 | v7placebo | rec | -0.03 | -0.29 |
| 2021 | v7placebo | rush | -0.05 | +0.00 |
| 2022 | v7 | rec | +0.47 | -0.09 |
| 2022 | v7 | rush | +0.46 | -0.13 |
| 2022 | v7placebo | rec | +0.00 | -0.25 |
| 2022 | v7placebo | rush | -0.04 | -0.14 |
| 2023 | v7 | rec | +0.43 | -0.08 |
| 2023 | v7 | rush | +0.46 | -0.01 |
| 2023 | v7placebo | rec | +0.02 | -0.24 |
| 2023 | v7placebo | rush | -0.05 | -0.21 |

## Results (Big-60 = union of all four models' pools)

| pool | A vs B | n | MAE A | MAE B | diff (A−B) | 95% CI | p(A not better) |
|---|---|---|---|---|---|---|---|
| big60 | v7 vs v5 | 5012 | 6.486 | 6.481 | +0.005 | [-0.005, +0.015] | 0.853 |
| big60 | v7placebo vs v5 | 5012 | 6.472 | 6.481 | -0.009 | [-0.017, -0.002] | 0.011 |
| big60 | v7 vs v7placebo | 5012 | 6.486 | 6.472 | +0.015 | [+0.002, +0.028] | 0.986 |
| big60 | v7 vs base | 5012 | 6.486 | 6.675 | -0.189 | [-0.241, -0.138] | 0.000 |
| all | v7 vs v5 | 25788 | 4.283 | 4.279 | +0.004 | [+0.001, +0.006] | 0.994 |
| all | v7placebo vs v5 | 25788 | 4.272 | 4.279 | -0.008 | [-0.009, -0.006] | 0.000 |
| all | v7 vs v7placebo | 25788 | 4.283 | 4.272 | +0.011 | [+0.008, +0.015] | 1.000 |
| all | v7 vs base | 25788 | 4.283 | 4.348 | -0.065 | [-0.082, -0.047] | 0.000 |
| big60, absent teammate (descriptive) | v7 vs v5 | 2075 | 6.530 | 6.517 | +0.013 | [-0.011, +0.035] | 0.853 |
| big60, absent teammate (descriptive) | v7placebo vs v5 | 2075 | 6.500 | 6.517 | -0.017 | [-0.025, -0.008] | 0.000 |
| big60, absent teammate (descriptive) | v7 vs v7placebo | 2075 | 6.530 | 6.500 | +0.030 | [+0.005, +0.054] | 0.991 |
| big60, absent teammate (descriptive) | v7 vs base | 2075 | 6.530 | 6.722 | -0.192 | [-0.277, -0.113] | 0.000 |

## Big-60 MAE by position (descriptive)

| model | QB | RB | WR | TE |
|---|---|---|---|---|
| base | 6.556 | 6.770 | 7.168 | 5.630 |
| v5 | 6.308 | 6.609 | 6.939 | 5.496 |
| v7placebo | 6.310 | 6.588 | 6.932 | 5.493 |
| v7 | 6.307 | 6.614 | 6.950 | 5.497 |

## Bias in Big-60 pool

| base | v5 | v7placebo | v7 |
|---|---|---|---|
| +0.79 | +0.08 | -0.03 | +0.14 |