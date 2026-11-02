# Validation: season 2024 (one-time, frozen model)

Model settings: `reports/opp_eff_params.json` (tuned on 2019–2023). Baseline: `ewma_hl8` (tuned on the same seasons).

## Headline (Big-60 = union of both models' own pools)

| pool | n | MAE model | MAE baseline | diff | 95% CI | p(model not better) |
|---|---|---|---|---|---|---|
| big60 | 1229 | 6.349 | 6.506 | -0.158 | [-0.265, -0.049] | 0.002 |
| all players | 6594 | 4.139 | 4.189 | -0.049 | [-0.078, -0.021] | 0.001 |
| big60 QB | 217 | 6.575 | 6.825 | -0.251 | [-0.459, -0.054] | 0.004 |
| big60 RB | 397 | 6.181 | 6.300 | -0.119 | [-0.218, -0.019] | 0.011 |
| big60 WR | 416 | 6.737 | 6.943 | -0.206 | [-0.386, -0.036] | 0.009 |
| big60 TE | 199 | 5.624 | 5.656 | -0.031 | [-0.197, +0.151] | 0.360 |

(Per-position rows are descriptive; with only 18 weekly clusters, their CIs are wide.)

## Secondary metrics (Big-60 union)

| model | MAE | RMSE | Spearman | bias |
|---|---|---|---|---|
| model | 6.349 | 8.044 | 0.354 | -0.37 |
| base | 6.506 | 8.170 | 0.317 | +0.32 |

## Weekly head-to-head on the baseline's own Big-60 (the CLAUDE.md format: their pool): model 15–3

| week | MAE model | MAE baseline | winner | record |
|---|---|---|---|---|
| 1 | 5.80 | 6.49 | model | 1–0 |
| 2 | 5.88 | 6.48 | model | 2–0 |
| 3 | 7.47 | 7.70 | model | 3–0 |
| 4 | 5.74 | 5.87 | model | 4–0 |
| 5 | 5.33 | 5.92 | model | 5–0 |
| 6 | 6.37 | 6.41 | model | 6–0 |
| 7 | 6.48 | 6.72 | model | 7–0 |
| 8 | 5.56 | 5.69 | model | 8–0 |
| 9 | 5.37 | 5.75 | model | 9–0 |
| 10 | 5.91 | 6.01 | model | 10–0 |
| 11 | 7.19 | 7.46 | model | 11–0 |
| 12 | 6.46 | 6.63 | model | 12–0 |
| 13 | 6.04 | 6.07 | model | 13–0 |
| 14 | 6.53 | 6.37 | baseline | 13–1 |
| 15 | 7.28 | 7.16 | baseline | 13–2 |
| 16 | 6.61 | 6.35 | baseline | 13–3 |
| 17 | 7.90 | 7.94 | model | 14–3 |
| 18 | 7.34 | 7.45 | model | 15–3 |

## Weekly head-to-head on the our own Big-60: model 11–7

| week | MAE model | MAE baseline | winner | record |
|---|---|---|---|---|
| 1 | 5.58 | 5.95 | model | 1–0 |
| 2 | 6.18 | 6.22 | model | 2–0 |
| 3 | 7.14 | 7.23 | model | 3–0 |
| 4 | 5.48 | 5.72 | model | 4–0 |
| 5 | 5.37 | 5.86 | model | 5–0 |
| 6 | 6.48 | 6.65 | model | 6–0 |
| 7 | 6.57 | 6.57 | baseline | 6–1 |
| 8 | 5.94 | 5.97 | model | 7–1 |
| 9 | 5.77 | 6.02 | model | 8–1 |
| 10 | 5.99 | 6.02 | model | 9–1 |
| 11 | 7.51 | 7.71 | model | 10–1 |
| 12 | 6.07 | 6.14 | model | 11–1 |
| 13 | 5.66 | 5.58 | baseline | 11–2 |
| 14 | 6.68 | 6.51 | baseline | 11–3 |
| 15 | 7.38 | 7.31 | baseline | 11–4 |
| 16 | 6.24 | 6.05 | baseline | 11–5 |
| 17 | 7.42 | 7.40 | baseline | 11–6 |
| 18 | 7.73 | 7.72 | baseline | 11–7 |