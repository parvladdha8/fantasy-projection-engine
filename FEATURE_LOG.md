# Feature log

Every candidate feature, kept or rejected (rigor rule 3). Evaluated on development seasons 2019–2023 unless noted. "Diff" = new − old MAE (negative = better). CI = 95% paired week-clustered bootstrap.

| Date | Feature | Pool | MAE before | MAE after | Diff | 95% CI | Verdict |
|---|---|---|---|---|---|---|---|
| 2026-11-01 | Snap-count zero games in history | Big-60 (union) | 6.762 | 6.743 | −0.019 | [−0.030, −0.009] | ✅ Kept |
| 2026-11-01 | Snap-count zero games in history | All players | 4.569 | 4.426 | −0.143 | [−0.151, −0.136] | ✅ Kept |
| 2026-11-01 | Opportunity × efficiency v1 (player volume EWMA × shrunk efficiency), forward-chained OOS 2020–23 | Big-60 (union) | 6.677 | 6.674 | −0.003 | [−0.042, +0.037] | ⚠️ Not significant on Big-60 |
| 2026-11-01 | Opportunity × efficiency v1, forward-chained OOS 2020–23 | All players | 4.348 | 4.313 | −0.035 | [−0.051, −0.018] | ✅ Significant on all players |

| 2026-11-01 | OE v2: volume shrinkage toward long-run average (narrow grid: hl_vol ≥ 2, hl_long ≥ 16), OOS 2020–23 | Big-60 vs v1 | 6.655 | 6.625 | −0.030 | [−0.043, −0.015] | ✅ Significant vs v1 |
| 2026-11-01 | OE v2, narrow grid | Big-60 vs baseline | 6.656 | 6.625 | −0.030 | [−0.068, +0.008] | ⚠️ p = 0.065, not significant |
| 2026-11-01 | OE v2, wide grid (hl_vol ≥ 1, hl_long ≥ 8), OOS 2020–23 | Big-60 vs v1 | 6.653 | 6.635 | −0.018 | [−0.033, −0.004] | ✅ Significant vs v1 |
| 2026-11-01 | OE v2, wide grid | Big-60 vs baseline | 6.653 | 6.635 | −0.018 | [−0.058, +0.020] | ❌ Not significant (p = 0.18) |
| 2026-11-01 | OE v2, wide grid | All players vs v1 | 4.313 | 4.320 | +0.007 | [+0.001, +0.014] | ❌ Slightly worse |

**Note on OE v2:** Widening the search grid made Big-60 results *worse*. The tuner chose more extreme settings (1-game recent memory) that reduce error across all players but not for starters. This shows the tuning objective is mismatched with the evaluation target. Both runs are logged so there's no cherry-picking of the better one.

**Note:** The first opportunity × efficiency run was *in-sample* (tuned and scored on 2019–2023): Big-60 −0.014, all −0.044. Those numbers are superseded by the forward-chained out-of-sample results above. The gap shows how much in-sample tuning flatters a model.

## Baseline weighting choices (dev seasons, Big-60 pool, complete data)

| Method | MAE | Verdict |
|---|---|---|
| EWMA half-life 8 games | 6.759 | ✅ Chosen |
| EWMA half-life 16 | 6.761 | ❌ Tied, not chosen (pre-stated rule: lowest MAE) |
| EWMA half-life 4 | 6.888 | ❌ |
| Career mean | 6.907 | ❌ |
| Last-8 mean | 7.025 | ❌ |
| EWMA half-life 2 | 7.242 | ❌ |
| Last-3 mean | 7.875 | ❌ |
| Last game | 10.214 | ❌ |
