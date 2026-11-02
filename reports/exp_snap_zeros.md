# Experiment: snap-count zero games (ewma_hl8, dev 2019–2023)

Zero games added in dev seasons: 3517 of 31280 scored player-games.

| pool | n | MAE old | MAE new | diff (new−old) | 95% CI | p(new not better) |
|---|---|---|---|---|---|---|
| big60 (union) | 5345 | 6.762 | 6.743 | -0.019 | [-0.030, -0.009] | 0.000 |
| all | 31280 | 4.569 | 4.426 | -0.143 | [-0.151, -0.136] | 0.000 |

## Bias (mean projection − actual; + = too high)

| pool | old | new |
|---|---|---|
| big60 (union) | +1.109 | +1.070 |
| all | +0.500 | +0.177 |

## Half-life re-check on complete data (each method's own big60 pool)

| method | MAE |
|---|---|
| ewma_hl8 | 6.759 |
| ewma_hl16 | 6.761 |
| ewma_hl4 | 6.888 |
| career_mean | 6.907 |
| last8_mean | 7.025 |
| ewma_hl2 | 7.242 |
| last3_mean | 7.875 |
| last_game | 10.214 |