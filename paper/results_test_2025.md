# Final test: season 2025 (one-time, frozen live model) — PASSED

Model: `predict()` with `reports/opp_eff_params.json` (tuned 2019–23, validated on 2024). Nothing tuned on 2025.

## Median (published projection) vs baseline (Big-60 = union of both pools; clusters = weeks)

| pool | n | MAE model | MAE baseline | diff | 95% CI | p(model not better) |
|---|---|---|---|---|---|---|
| **big60 (headline)** | 1224 | 6.295 | 6.589 | -0.294 | [-0.410, -0.185] | 0.000 |
| all players | 6663 | 4.024 | 4.170 | -0.146 | [-0.178, -0.115] | 0.000 |
| big60 QB (descriptive) | 203 | 6.670 | 6.789 | -0.118 | [-0.255, +0.020] | 0.043 |
| big60 RB (descriptive) | 386 | 6.343 | 6.663 | -0.320 | [-0.450, -0.195] | 0.000 |
| big60 WR (descriptive) | 419 | 6.452 | 6.772 | -0.320 | [-0.525, -0.123] | 0.001 |
| big60 TE (descriptive) | 216 | 5.554 | 5.915 | -0.361 | [-0.628, -0.120] | 0.001 |

## Mean projection (v5) vs baseline (secondary; the 2024 validation's headline)

| pool | n | MAE mean | MAE baseline | diff | 95% CI | p |
|---|---|---|---|---|---|---|
| big60 | 1224 | 6.400 | 6.589 | -0.189 | [-0.270, -0.112] | 0.000 |
| all players | 6663 | 4.094 | 4.170 | -0.076 | [-0.101, -0.054] | 0.000 |

## Secondary metrics (Big-60 union)

| projection | MAE | RMSE | Spearman | bias (proj − actual) |
|---|---|---|---|---|
| median | 6.295 | 8.196 | 0.372 | -0.42 |
| mean (v5) | 6.400 | 8.170 | 0.373 | +0.49 |
| baseline | 6.589 | 8.335 | 0.348 | +1.11 |

## Floor–ceiling coverage (target ~80%)

| pool | n | inside | below floor | above ceiling |
|---|---|---|---|---|
| big60 | 1224 | 82.7% | 8.3% | 9.1% |
| all players | 6663 | 80.1% | 10.7% | 9.2% |
| big60 QB | 203 | 75.9% | 15.3% | 8.9% |
| big60 RB | 386 | 82.6% | 6.2% | 11.1% |
| big60 WR | 419 | 85.4% | 8.1% | 6.4% |
| big60 TE | 216 | 83.8% | 5.6% | 10.6% |

## Weekly head-to-head on the baseline's own Big-60 (the CLAUDE.md format): model 16–2

| week | MAE model | MAE baseline | winner | record |
|---|---|---|---|---|
| 1 | 5.18 | 5.56 | model | 1–0 |
| 2 | 5.95 | 6.55 | model | 2–0 |
| 3 | 5.89 | 6.54 | model | 3–0 |
| 4 | 5.48 | 6.23 | model | 4–0 |
| 5 | 5.53 | 5.21 | baseline | 4–1 |
| 6 | 6.89 | 7.26 | model | 5–1 |
| 7 | 8.03 | 8.01 | baseline | 5–2 |
| 8 | 6.54 | 6.85 | model | 6–2 |
| 9 | 5.92 | 6.20 | model | 7–2 |
| 10 | 6.75 | 6.84 | model | 8–2 |
| 11 | 6.59 | 6.96 | model | 9–2 |
| 12 | 6.95 | 7.40 | model | 10–2 |
| 13 | 5.60 | 5.84 | model | 11–2 |
| 14 | 6.20 | 6.57 | model | 12–2 |
| 15 | 6.74 | 6.94 | model | 13–2 |
| 16 | 7.14 | 7.31 | model | 14–2 |
| 17 | 6.37 | 7.11 | model | 15–2 |
| 18 | 6.64 | 7.22 | model | 16–2 |

## Weekly head-to-head on the our own Big-60: model 15–3

| week | MAE model | MAE baseline | winner | record |
|---|---|---|---|---|
| 1 | 5.00 | 5.48 | model | 1–0 |
| 2 | 6.11 | 6.25 | model | 2–0 |
| 3 | 6.16 | 6.48 | model | 3–0 |
| 4 | 5.67 | 6.40 | model | 4–0 |
| 5 | 5.51 | 5.34 | baseline | 4–1 |
| 6 | 6.62 | 6.84 | model | 5–1 |
| 7 | 7.93 | 7.92 | baseline | 5–2 |
| 8 | 6.23 | 6.67 | model | 6–2 |
| 9 | 5.98 | 6.17 | model | 7–2 |
| 10 | 5.87 | 5.94 | model | 8–2 |
| 11 | 7.03 | 7.03 | model | 9–2 |
| 12 | 6.83 | 7.16 | model | 10–2 |
| 13 | 5.49 | 5.62 | model | 11–2 |
| 14 | 6.65 | 6.93 | model | 12–2 |
| 15 | 6.90 | 7.10 | model | 13–2 |
| 16 | 7.31 | 7.23 | baseline | 13–3 |
| 17 | 6.51 | 7.17 | model | 14–3 |
| 18 | 6.99 | 7.44 | model | 15–3 |
