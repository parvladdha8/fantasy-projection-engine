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

| 2026-11-01 | Tuning target = fantasy-relevant players (option A), OE v2, OOS 2020–23 | **Big-60 vs baseline** | 6.656 | 6.601 | **−0.055** | [−0.093, −0.014] | ✅ **Significant (p = 0.004)** |
| 2026-11-01 | Option A, OE v2 | Big-60 vs v2 tuned on all players | 6.634 | 6.601 | −0.032 | [−0.054, −0.010] | ✅ Significant |
| 2026-11-01 | Option A: volume shrinkage on vs off | Big-60, v2_rel vs v1_rel | 6.612 | 6.601 | −0.011 | [−0.019, −0.002] | ✅ Significant (still earns its place) |
| 2026-11-01 | Option A, OE v2 | All players vs baseline | 4.348 | 4.360 | +0.013 | [−0.002, +0.028] | ➖ Slightly worse on fringe players (expected; not our target) |

| 2026-11-01 | **Ablation** (same framework, relevant-player tuning): decomposition alone | Big-60 vs baseline | 6.648 | 6.651 | +0.003 | [−0.025, +0.031] | ❌ No gain by itself |
| 2026-11-01 | Ablation: + efficiency shrinkage | Big-60 vs no-shrinkage OE | 6.651 | 6.597 | −0.054 | [−0.088, −0.022] | ✅ Main source of gain |
| 2026-11-01 | Ablation: + volume shrinkage | Big-60 vs v1 | 6.597 | 6.587 | −0.011 | [−0.020, −0.001] | ✅ Kept |

| 2026-11-01 | Team context v3: volume = shrunk share × team's historical average volume | **Big-60 vs v2** | 6.621 | 6.629 | +0.009 | [−0.019, +0.035] | ❌ **Rejected for now** (no Big-60 gain) |
| 2026-11-01 | Team context v3 | All players vs v2 | 4.360 | 4.352 | −0.009 | [−0.016, −0.002] | ➖ Small gain on fringe players; not our target |

**Note on team context:** Code kept (`team_context.py`, `CompParams.team`) because betting lines and injury reallocation need the share × team-volume structure. Re-test it once team volume is forward-looking (betting lines) rather than a backward-looking average.

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
