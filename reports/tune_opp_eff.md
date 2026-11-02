# Opportunity × efficiency tuning (dev 2019–2023)

## rec: best hl_vol=4, hl_eff=6, k=25 (MSE 23.7963)

Top 5:

- MSE 23.7963: hl_vol=4, hl_eff=6, k=25
- MSE 23.8004: hl_vol=4, hl_eff=8, k=25
- MSE 23.8124: hl_vol=4, hl_eff=8, k=50
- MSE 23.8129: hl_vol=4, hl_eff=4, k=25
- MSE 23.8138: hl_vol=4, hl_eff=6, k=50

MSE vs k (best half-lives): k=0: 24.1208, k=10: 23.8369, k=25: 23.7963, k=50: 23.8138, k=100: 23.8743, k=200: 23.9545, k=400: 24.0263, k=800: 24.0765

## rush: best hl_vol=3, hl_eff=4, k=100 (MSE 7.0089)

Top 5:

- MSE 7.0089: hl_vol=3, hl_eff=4, k=100
- MSE 7.0094: hl_vol=3, hl_eff=6, k=100
- MSE 7.0112: hl_vol=3, hl_eff=3, k=100
- MSE 7.0119: hl_vol=3, hl_eff=8, k=100
- MSE 7.0129: hl_vol=3, hl_eff=4, k=50

MSE vs k (best half-lives): k=0: 7.2605, k=10: 7.0953, k=25: 7.0399, k=50: 7.0129, k=100: 7.0089, k=200: 7.0260, k=400: 7.0517, k=800: 7.0742

## pass: best hl_vol=3, hl_eff=6, k=50 (MSE 4.8939)

Top 5:

- MSE 4.8939: hl_vol=3, hl_eff=6, k=50
- MSE 4.8959: hl_vol=3, hl_eff=6, k=25
- MSE 4.8989: hl_vol=3, hl_eff=4, k=50
- MSE 4.8995: hl_vol=3, hl_eff=8, k=50
- MSE 4.9005: hl_vol=3, hl_eff=8, k=25

MSE vs k (best half-lives): k=0: 4.9437, k=10: 4.9092, k=25: 4.8959, k=50: 4.8939, k=100: 4.9089, k=200: 4.9501, k=400: 5.0178, k=800: 5.0960

## other: best hl=128 (hl8: 0.2380, hl16: 0.2357, hl32: 0.2350, hl64: 0.2348, hl128: 0.2348)