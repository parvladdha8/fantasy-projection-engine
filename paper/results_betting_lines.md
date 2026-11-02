# Betting lines: result, placebo, and clean ablation

All runs: forward-chained out-of-sample 2020–2023 (each season tuned on dev seasons before it), relevant-player tuning loss, Big-60 = union of each run's models' own weekly pools, paired bootstrap resampling whole season-weeks. Δ < 0 = lower error.

Source data: nflverse closing spread and over/under (complete for all 2,127 regular-season games 2018–2025). Closing lines are known at kickoff, when projections freeze.

## 1. Clean ablation: headline (`uv run python scripts/exp_betting_lines.py --ablation`)

| Model | Big-60 MAE | All-players MAE | Big-60 bias |
|---|---|---|---|
| Baseline (trailing weighted average) | 6.659 | 4.348 | +0.85 |
| v2: opp × eff with efficiency + volume shrinkage | 6.607 | 4.360 | +0.47 |
| v4-reg: + team context, team volume = regression on team history only | 6.585 | 4.341 | +0.33 |
| **v4: + betting lines in the team-volume regression (current model)** | **6.540** | **4.326** | +0.33 |

| Contribution (Big-60) | Δ MAE | 95% CI | p (not better) |
|---|---|---|---|
| **Betting-market information** (v4 vs v4-reg) | **−0.045** | [−0.060, −0.031] | < 0.001 |
| Team-volume shrinkage (v4-reg vs v2) | −0.022 | [−0.052, +0.006] | 0.070 |
| Total (v4 vs v2) | −0.068 | [−0.104, −0.033] | < 0.001 |
| **v4 vs baseline** | **−0.119** | [−0.163, −0.077] | < 0.001 |

Big-60 MAE by position (descriptive): QB 6.580 → 6.390, RB 6.721 → 6.616, WR 7.169 → 7.034, TE 5.593 → 5.552 (baseline → v4).

## 2. Placebo: lines shuffled between team-games within each season (`--placebo`)

| Comparison (Big-60) | Real lines | Shuffled lines |
|---|---|---|
| v4 vs v2 | −0.066 [−0.101, −0.032] | −0.017 [−0.049, +0.014] (n.s.) |
| v4 vs v3 (team context, historical average) | −0.073 | −0.024 [−0.037, −0.010] |

Reading: the large gain vanishes with shuffled lines, so there's no look-ahead leakage. The remaining placebo gain over v3 is the team-volume regression's shrinkage toward the league average, which motivated the clean ablation above.

## 3. Fitted team-volume regression (2018–2023, final half-lives)

| Team stat | Half-life (games) | Intercept | History | Implied points | Expected margin | R² |
|---|---|---|---|---|---|---|
| Targets | 8 | 2.81 | 0.573 | +0.488 | −0.214 | 0.104 |
| Carries | 4 | 20.34 | 0.455 | −0.254 | +0.274 | 0.078 |
| Pass attempts | 16 | 3.48 | 0.550 | +0.517 | −0.237 | 0.083 |

Interpretation: a 7-point favourite runs about 1.9 more times and is targeted about 1.5 fewer times than in an even game (game script). Each implied point adds about 0.5 targets. The history coefficient of about 0.5 shrinks team volume roughly halfway toward the league mean. About 90% of weekly team volume is unpredictable before kickoff.

## Caveats
- Closing lines include all pre-kickoff information (injuries, weather). Live projections must snapshot lines before kickoff from a verified source. Lines captured earlier may be slightly less informative.
- Several variants were tried on dev seasons. The one-time 2024 validation is the real check.
