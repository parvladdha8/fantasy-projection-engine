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

| 2026-11-01 | Betting lines v4 (team volume = OLS on history + implied pts + margin), first run | Big-60 vs v2 | 6.622 | 6.557 | −0.066 | [−0.101, −0.032] | ⚠️ Bundled two changes (see placebo) |
| 2026-11-01 | **Placebo**: v4 with lines shuffled within season | Big-60 vs v2 | 6.609 | 6.592 | −0.017 | [−0.049, +0.014] | ✅ No leakage; revealed the regression confound |
| 2026-11-01 | Team-volume regression on history only (v4-reg) | Big-60 vs v2 | 6.607 | 6.585 | −0.022 | [−0.052, +0.006] | ⚠️ p = 0.07 on Big-60; significant on all players (−0.019) |
| 2026-11-01 | **Betting-market information** (v4 vs v4-reg) | **Big-60** | 6.585 | 6.540 | **−0.045** | [−0.060, −0.031] | ✅ **Kept** |
| 2026-11-01 | v4 (current) vs baseline | Big-60 | 6.659 | 6.540 | −0.119 | [−0.163, −0.077] | ✅ Superseded by v5 |

| 2026-11-02 | Calibration-only efficiency multiplier (v5-cal, α only) | Big-60 vs v4 | 6.550 | 6.529 | −0.021 | [−0.037, −0.006] | ➖ Control; helps, but not tested as its own feature |
| 2026-11-02 | **Betting lines for efficiency** (v5 vs v5-cal: β · implied points) | **Big-60** | 6.529 | 6.477 | **−0.052** | [−0.071, −0.033] | ✅ **Kept** (pre-registered headline) |
| 2026-11-02 | v5 vs v4 | Big-60 | 6.550 | 6.477 | −0.072 | [−0.095, −0.051] | ✅ Adoption rule met |
| 2026-11-02 | v5 (current) vs baseline | Big-60 | 6.666 | 6.477 | −0.188 | [−0.242, −0.138] | ✅ **Current model** |
| 2026-11-02 | **2024 VALIDATION** (one-time, frozen v5) vs baseline | Big-60 | 6.506 | 6.349 | **−0.158** | [−0.265, −0.049] | ✅ **Passed (p = 0.002)** |
| 2026-11-02 | Week-of-season effect v6 (γ per position × wk 1–4/5–12/13–18, EB-shrunk) | **Big-60 vs v6-pos** | 6.473 | 6.480 | **+0.007** | [−0.000, +0.016] | ❌ **Rejected** (pre-registered headline) |
| 2026-11-02 | Week-of-season v6 | Big-60 weeks 13–18 vs v5 (descriptive) | 6.543 | 6.564 | +0.021 | [−0.003, +0.046] | ❌ Worse late even though it fixed late bias |
| 2026-11-02 | Position-only recalibration (v6-pos control) | Big-60 vs v5 | 6.484 | 6.473 | −0.011 | [−0.025, +0.005] | ❌ Not significant (p = 0.086); not adopted |
| 2026-11-02 | Vacated opportunity v7 (teammates Out/Doubtful → share × (1 + λ·V)) | **Big-60 vs v5** | 6.481 | 6.486 | **+0.005** | [−0.005, +0.015] | ❌ **Rejected** (pre-registered headline) |
| 2026-11-02 | v7, Big-60 games with an absent teammate (descriptive) | vs v5 | 6.517 | 6.530 | +0.013 | [−0.011, +0.035] | ❌ No gain even where it applies |
| 2026-11-02 | v7 placebo (absences moved to random teams) | Big-60 vs v5 | 6.481 | 6.472 | −0.009 | [−0.017, −0.002] | ⚠️ Placebo "helped": acts as downward recalibration (see DECISIONS) |
| 2026-11-02 | **Median calibration v8** (a + b·proj per position, least absolute deviations) | **Big-60 vs v5** | 6.484 | 6.429 | **−0.054** | [−0.097, −0.012] | ✅ **Adopted** (p = 0.006) |
| 2026-11-02 | Mechanism: v8 (median) vs v8-ols (mean recalibration) | Big-60 | 6.458 | 6.429 | −0.029 | [−0.066, +0.007] | ⚠️ p = 0.064: "median targeting" claim not established |
| 2026-11-02 | Least-squares recalibration (v8-ols control) | Big-60 vs v5 | 6.484 | 6.458 | −0.026 | [−0.044, −0.007] | ➖ Control; plain recalibration helps too |
| 2026-11-02 | v8 | All players vs v5 | 4.279 | 4.308 | +0.029 | [+0.012, +0.046] | ⚠️ Worse on fringe players (map extrapolated outside the range it was fitted on) |
| 2026-11-02 | v8 (current) vs baseline | Big-60 | 6.678 | 6.429 | −0.249 | [−0.324, −0.174] | ✅ Superseded by v8m |
| 2026-11-02 | **Percentage-only median calibration v8m** (b·proj, no intercept) | **Big-60 vs v5** | 6.484 | 6.430 | **−0.054** | [−0.099, −0.011] | ✅ **Adopted** (p = 0.007) |
| 2026-11-02 | v8m (safety check) | **All players vs v5** | 4.279 | 4.212 | **−0.067** | [−0.078, −0.058] | ✅ Fringe-player problem fixed |
| 2026-11-02 | v8m vs v8 | Big-60 | 6.429 | 6.430 | +0.000 | [−0.009, +0.009] | ✅ Same on top players, simpler |
| 2026-11-02 | v8m (current) vs baseline | Big-60 / all | 6.678 / 4.348 | 6.430 / 4.212 | −0.249 / −0.136 | [−0.326, −0.172] | ✅ **Current model** |
| 2026-11-02 | Vacated opportunity re-tested on top of v8m (v7m; final, pre-specified) | **Big-60 vs v8m** | 6.430 | 6.428 | **−0.002** | [−0.012, +0.008] | ❌ **Rejected (final)** |
| 2026-11-02 | v7m placebo | Big-60 vs v8m | 6.430 | 6.433 | +0.003 | [−0.003, +0.009] | ✅ Placebo gain gone once calibration is in the model |
| 2026-11-02 | **Floor/ceiling v9** (10th/90th pct = position % of mean projection) | Big-60 coverage | target 80% | 80.8% (9.6% / 9.5% tails) | — | — | ✅ **Calibrated** |
| 2026-11-02 | Floor/ceiling v9 | Big-60 interval score vs baseline-centred benchmark | 28.946 | 28.515 | −0.431 | [−0.659, −0.211] | ✅ **Adopted** |
| 2026-11-02 | Floor/ceiling v9 | All-players coverage | target 80% | 51.4% (32.0% below floor) | — | — | ⚠️ Badly miscalibrated for fringe players |
| 2026-11-02 | **Floor/ceiling v10** (a + b·proj + c·proj·volatility, fitted on all players) | Coverage Big-60 / all | target 80% | **82.5% / 79.0%** (tails 7.2/10.3, 11.5/9.5) | — | — | ✅ **Calibrated in both pools** |
| 2026-11-02 | v10 vs v9 | Interval score, all players | 20.987 | 18.793 | −2.193 | [−2.355, −2.045] | ✅ Fringe problem fixed |
| 2026-11-02 | v10 vs v9 | Interval score, Big-60 | 28.515 | 28.486 | −0.029 | [−0.199, +0.134] | ✅ Not worse on top players |
| 2026-11-02 | **Per-player spread** (v10 vs v10-novol) | Interval score, Big-60 | 28.912 | 28.486 | **−0.426** | [−0.559, −0.304] | ✅ **Adopted** |
| 2026-11-02 | v10-novol (projection level only) | Big-60 coverage | target 80% | 85.3% (5.6% below) | — | — | ❌ Too wide for top players without volatility |
| 2026-11-02 | **Week 1 effect v11** (Week 1 median × (1 + γ_pos), LAD, EB-shrunk to 0) | **Big-60 Week 1 vs v8m** (game-clustered) | 6.158 | 6.105 | **−0.053** | [−0.192, +0.084] | ❌ **Not adopted** (p = 0.21; pre-registered headline) |
| 2026-11-02 | Week 1 effect v11 (secondary) | All players Week 1 vs v8m | 4.459 | 4.416 | −0.043 | [−0.076, −0.009] | ⚠️ Significant (p = 0.006) but not the headline; does not override the rule |
| 2026-11-02 | Player-specific Week 1 effect v11p (partial pooling toward position) | Big-60 Week 1 vs v11 | 6.105 | 6.272 | +0.167 | [+0.065, +0.270] | ❌ **Rejected**: worse |
| 2026-11-02 | **Week 1 effect v11, bug-fix re-run** (fitted on calibrated seasons ≥ 2020 only; final dev test) | **Big-60 Week 1 vs v8m** | 6.177 | 6.167 | **−0.010** | [−0.039, +0.017] | ❌ **Not adopted (p = 0.22); idea closed on dev data** |
| 2026-11-02 | v11p, bug-fix re-run | Big-60 Week 1 vs v11 | 6.167 | 6.220 | +0.054 | [+0.002, +0.133] | ❌ **Rejected** again: worse |
| 2026-11-02 | **Prime-time effect v12** (kickoff ≥ 19:00 ET: median × (1 + γ_pos), EB-shrunk to 0) | **Big-60 prime-time vs v8m** | 6.414 | 6.442 | **+0.028** | [−0.022, +0.082] | ❌ **Rejected** (pre-registered headline) |
| 2026-11-02 | Prime-time placebo (label on random games) | Big-60 placebo games vs v8m | 6.318 | 6.403 | +0.085 | [+0.012, +0.162] | ⚠️ Placebo fitted γ as negative as the real one → exposed a fitting bug (see DECISIONS) |
| 2026-11-02 | Player "prime-time splits" v12p | Big-60 prime-time vs v12 | 6.442 | 6.463 | +0.021 | [−0.054, +0.094] | ❌ **Rejected** |
| 2026-11-02 | **Bad-weather effect v13** (outdoor AND (wind ≥ 15 mph OR temp ≤ 32°F): median × (1 + γ_pos), EB-shrunk, fitted on seasons ≥ 2020) | **Big-60 bad weather vs v8m, 2021–23** | 5.931 | 5.970 | **+0.039** | [−0.035, +0.118] | ❌ **Rejected** (pre-registered headline) |
| 2026-11-02 | Weather placebo (label on random games) | Big-60 placebo games vs v8m | 6.036 | 6.105 | +0.070 | [−0.021, +0.167] | Procedure alone doesn't help |
| 2026-11-02 | Weather placebo (label on random outdoor games) | Big-60 placebo games vs v8m | 6.209 | 6.209 | +0.000 | – | Fully shrunk to 0 (B = 1) every fold |

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
