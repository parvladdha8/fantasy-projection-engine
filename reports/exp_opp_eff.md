# Experiment: opportunity × efficiency vs baseline, forward-chaining out-of-sample

## Settings chosen in each fold (OE given as hl_vol/hl_eff/k)

| scored season | tuned on | baseline method | rec | rush | pass |
|---|---|---|---|---|---|
| 2020 | 2019–2019 | ewma_hl4 | 4/8/100 | 3/64/100 | 3/6/25 |
| 2021 | 2019–2020 | ewma_hl8 | 4/6/25 | 3/16/100 | 4/6/25 |
| 2022 | 2019–2021 | ewma_hl8 | 4/6/25 | 3/8/100 | 4/6/25 |
| 2023 | 2019–2022 | ewma_hl8 | 4/6/25 | 3/6/100 | 4/6/25 |

## Out-of-sample results, seasons 2020–2023 pooled

| pool | n | MAE base | MAE OE | diff (OE−base) | 95% CI | p(OE not better) | bias base | bias OE |
|---|---|---|---|---|---|---|---|---|
| big60 (union) | 4751 | 6.677 | 6.674 | -0.003 | [-0.042, +0.037] | 0.454 | +0.97 | +0.78 |
| all | 25788 | 4.348 | 4.313 | -0.035 | [-0.051, -0.018] | 0.000 | +0.20 | +0.21 |
| big60 QB | 778 | 6.556 | 6.551 | -0.006 | [-0.088, +0.081] | 0.427 | +1.03 | +0.68 |
| big60 RB | 1568 | 6.700 | 6.722 | +0.022 | [-0.051, +0.099] | 0.708 | +0.92 | +0.80 |
| big60 WR | 1601 | 7.221 | 7.184 | -0.037 | [-0.103, +0.031] | 0.146 | +1.12 | +0.82 |
| big60 TE | 804 | 5.662 | 5.683 | +0.021 | [-0.056, +0.101] | 0.704 | +0.69 | +0.75 |

## Shrinkage share in the Big-60 pool (k / (opportunities + k); 1 = all league average)

| component | position | median | 10th pct | 90th pct |
|---|---|---|---|---|
| rec | RB | 0.49 | 0.34 | 0.75 |
| rec | WR | 0.26 | 0.21 | 0.54 |
| rec | TE | 0.33 | 0.25 | 0.64 |
| rush | QB | 0.64 | 0.42 | 0.83 |
| rush | RB | 0.37 | 0.21 | 0.51 |
| pass | QB | 0.07 | 0.07 | 0.10 |