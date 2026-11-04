# Decisions log

Format: date, decision, and the reason. Parv's economic reasoning goes here so every choice can be defended.

---

### 2026-11-01: Environment: uv + project-local Python 3.12
**Decision:** Use `uv` with a project virtual environment (`.venv`) and Python 3.12. Exact package versions are pinned in `uv.lock`.
**Reason:** macOS ships Python 3.9, which is too old for current data libraries, and CLAUDE.md forbids installing into system Python. The lock file makes results reproducible: anyone rerunning the backtest gets the same package versions.

### 2026-11-01: Data split
**Decision:** 2018 = burn-in (history only, never scored). 2019–2023 = development (tuning allowed). 2024 = validation. 2025 = final test, used once.
**Reason:** A trailing average needs past games, so 2018 Week 1 has no fair projection. Using 2018 only as history keeps every scored projection on equal footing. Holding out 2024/2025 means our reported error isn't inflated by tuning to the test data (overfitting).

### 2026-11-01: Regular season only, skill positions only
**Decision:** Baseline history and scoring use regular-season QB/RB/WR/TE games. Playoff games are excluded.
**Reason:** Redraft fantasy leagues are played in the regular season. Playoff games are few and come from a selected group of teams (survivorship).

### 2026-11-01: Our own PPR scoring formula
**Decision:** Compute full-PPR points from box-score stats ourselves (see `scoring.py`).
**Reason:** Rigor rule 5 requires every source to use identical scoring. Check: our formula matches nflverse's `fantasy_points_ppr` on all 47,788 skill-position rows (max difference 0.00).

### 2026-11-01: Team label alias OAK → LV
**Decision:** Treat `OAK` (schedules, 2018–2019) and `LV` (stats) as the same franchise.
**Reason:** It's the same team relabeled after the 2020 move. This was the only cause of the schedule-vs-stats mismatch (32 team-games).

### 2026-11-01: Extreme games kept, not removed
**Decision:** Keep all real extreme games (e.g. Tyreek Hill 57.9, 2020 Wk 12; Sam Darnold −6.7, 2019 Wk 7). The quality check fails only on impossible values (< −15 or > 80).
**Reason:** These are real outcomes. Deleting them would make our errors look smaller than they are. Each flagged game was checked against the box score.

### 2026-11-01: Known data limitation: players who played but recorded no stats
**Status: FIXED 2026-11-01. See "Snap-count zero games" below.**
**Original decision:** Accept that nflverse weekly stats only include a player-week if he recorded a stat. An active WR with 0 targets is mostly missing rather than listed at 0 points.
**Effect:** Trailing averages skip some true zero games, so they lean slightly high for fringe players. Evaluation also leaves out some zero games. The effect is small for Big-60-calibre players.
**Planned fix (Phase 2):** Join snap counts so any player with offensive snaps gets a row, using 0 when he had no stats.

### 2026-11-01: Baseline = EWMA of past PPR points, half-life 8 games
**Decision:** The official naive baseline is an exponentially weighted moving average of a player's previous regular-season games (crossing seasons), with weights halving every 8 games.
**Reason:** It had the lowest MAE on the Big-60-style pool in development seasons (6.745). That pool is the one we're graded on. Compared to: half-life 16 (6.760), 4 (6.864), career mean (6.895), last-8 mean (6.997), half-life 2 (7.222), last-3 mean (7.850), last game (10.158).
**Economics:** This is the classic bias–variance tradeoff. A short memory (last game) reacts to noise. A very long memory (career mean) misses real changes in role. A half-life of 8 games is about half a season.
**Caveat:** The gap between half-lives 8 and 16 (0.015 pts) is tiny and almost certainly not statistically meaningful. We chose 8 by the pre-stated rule (lowest Big-60 MAE). On the all-players pool, half-life 4 was marginally best (4.726 vs 4.752).

### 2026-11-01: Big-60-style evaluation pool selected by OUR projection
**Decision:** For baseline scoring, each week's pool is the top 10 QB / 20 RB / 20 WR / 10 TE by the baseline's own pre-game projection, restricted to players who played that week.
**Reason:** It mirrors the leaderboard format, and the pool is chosen using only pre-game information, never by actual points. "Played that week" is a stand-in for the inactive-player policy (excluded if inactive at kickoff) until we have injury/active data.

### 2026-11-01: Snap-count zero games added (Phase 2, step 1)
**Decision:** Any QB/RB/WR/TE with at least 1 offensive snap but no stats row gets a 0-point game (`player_games.py`). Snap counts (Pro Football Reference IDs) are linked to nflverse IDs through the nflverse players table.
**Matching rules:** Match on (player ID, game) only, and take position from nflverse. PFR labels some backs as FB/HB and two-way players oddly, which caused all 521 apparent mismatches. Stats rows are never dropped, because a recorded stat proves the player played. Players with only special-teams snaps get no row: they weren't part of the offense.
**Scale:** 6,245 zero games added (8 seasons), mostly blocking TEs (median 8 snaps). Some are real starters who were shut out (Cade Otton, 92% of snaps, 0 pts). The ID match rate is 99.84%. The unmatched rows are fringe players with 1–9 snaps.
**Evidence (dev 2019–2023, EWMA hl8, same games scored for both versions, paired bootstrap resampling whole weeks):**
- Big-60 pool: MAE 6.762 → 6.743, diff −0.019, 95% CI [−0.030, −0.009]. Significant.
- All players: MAE 4.569 → 4.426, diff −0.143, CI [−0.151, −0.136]. Upward bias drops from +0.50 to +0.18 pts.
**Economics:** This is sample-selection bias. Recording only games where something happened is like measuring wages only for people who have jobs. The average ends up conditioned on a good outcome, so it runs too high.
**Note on headline numbers:** The official Big-60 baseline MAE moved from 6.745 to 6.759 because the evaluation set now *includes* the hard-to-predict zero games, not because projections got worse. Phase 1 and Phase 2 MAEs are not directly comparable. Same-pool comparisons (above) are the valid ones.

### 2026-11-01: Significance test = paired, week-clustered bootstrap
**Decision:** Compare two models with a paired bootstrap on per-player-game absolute errors, resampling whole season-weeks (2,000 draws).
**Reason:** It's paired because both models predict the same games, so we compare their errors game by game, which cancels out "this game was just hard to predict." It resamples whole weeks because errors within a week are correlated (weather, league-wide scoring swings). Treating 30,000 rows as independent would make every tiny gain look significant.

### 2026-11-01: Finding: Big-60 pool is projected ~1.1 pts too high
**Observation:** Selecting each week's top players *by projection* picks players whose recent averages were inflated by luck. On average they then score about 1.07 pts less than projected.
**Implication:** This is regression to the mean (the winner's curse), and it's the core motivation for shrinkage in Phase 2. The fix is to estimate how much of a hot streak is signal and how much is noise, rather than adding a hand-tuned "subtract 1 point."

### 2026-11-01: Opportunity × efficiency v1: design
**Decision:** Projection = Σ (expected volume × expected points per opportunity) over receiving (targets), rushing (carries) and passing (attempts), plus "other" (fumbles, return TDs). Volume is an EWMA of the player's past games. Efficiency is shrunk toward the position's league rate: eff = (S_pts + k·μ) / (S_opp + k).
**Reason:** Volume is mostly set by the coaches (role, depth chart) and is stable. Efficiency, especially touchdowns, is noisy. Separating them lets each have its own memory length and its own degree of skepticism. k has a natural reading: "how many league-average opportunities of evidence our prior is worth."
**Leakage control:** The league rate μ uses only weeks before the projected week, for all players. A test changes every player's week-4 stats and confirms that no week ≤ 4 projection moves.

### 2026-11-01: Validation = forward-chaining (walk-forward) over dev seasons
**Decision:** To score season s ∈ {2020…2023}, tune every model (ours and the baseline) only on dev seasons < s. Pool the four out-of-sample seasons and compare with the paired bootstrap.
**Reason:** Tuning and scoring on the same seasons overstates performance (in-sample optimism). Forward-chaining also never uses future seasons to set parameters, which matches the no-look-ahead rule. Cost: 2019 is never scored (it is only ever training data).

### 2026-11-01: Opportunity × efficiency v1: result
**Out-of-sample (2020–2023):** It beats the baseline on all players (−0.035 MAE, significant), but **not on the Big-60** (−0.003, CI [−0.042, +0.037]). By position: WR −0.037 (not significant), RB +0.022, TE +0.021, QB −0.006.
**Tuned settings (stable across folds once ≥2 training seasons):** Receiving: volume half-life 4 games, efficiency half-life 6, k = 25 targets. Rushing: 3 / 6–16 / k = 100 carries. Passing: 4 / 6 / k = 25 attempts.
**Interpretation:** Rushing needs about 4× more shrinkage than receiving (k = 100 vs 25). That's consistent with yards per carry being mostly a product of the offensive line and game situation rather than the back, a well-known finding in football analytics. QB passing efficiency is barely shrunk (about 7%), because QBs pile up hundreds of attempts.
**Why it doesn't help the Big-60 yet (hypotheses to test next):**
1. **Volume isn't shrunk.** The short volume memory (half-life 3–4) chases hot streaks, and the Big-60 selection picks exactly those players. Big-60 bias is still +0.78 pts.
2. **Volume ignores team context.** A player's raw targets mix his *share* with his *team's* pass volume. The real edge of opportunity modeling is share × team volume, where team volume can later use betting lines.
3. **The tuning loss counts all players equally.** The tuning data is dominated by low-usage players, while the Big-60 is about starters.

### 2026-11-01: OE v2: volume shrinkage: result and lesson
**Design:** vol = (S_recent + m · long_run) / (W_recent + m). The player's short-memory volume is shrunk toward his own long-run volume with m pseudo-games. m = 0 is v1, so the v2 search nests v1.
**Result (forward-chained OOS 2020–23):** Volume shrinkage beats v1 on the Big-60 in both grid versions (−0.030 narrow, −0.018 wide; both significant). Against the baseline it's not significant in either (p = 0.065 narrow, 0.18 wide). Big-60 bias: baseline +0.95, v1 +0.77, v2 +0.69.
**Lesson:** Widening the grid *hurt* out-of-sample Big-60 error. The tuner minimises squared error over **all** player-games, which are mostly backups and fringe players with volatile roles, so it rewards very fast memories. Starters' roles are more stable. The tuning objective doesn't match what we're graded on.
**Multiple-comparisons caution:** Per-position results (e.g. WR p = 0.036) come from 4 positions × 2 comparisons × several runs. Individual position "wins" at p ≈ 0.03 should not be quoted as findings.
**Open decision (for Parv):** What loss should the tuner minimise? Resolved in the next entry.

### 2026-11-01: Tuning target = fantasy-relevant players (option A), chosen by Parv
**Decision:** Model settings are tuned to minimise squared error only on "relevant" player-games: each week's top 15 QB / 30 RB / 30 WR / 15 TE by the fixed EWMA-hl8 baseline's **pre-game** projection (12,600 of 51,938 player-games).
**Reason (economics):** Estimate the model on the population you'll predict for. Backups have volatile roles and reward jumpy settings; starters have stable roles. The pool is a bit wider than the Big-60 to give more data and to avoid tuning only on players right at the cutoff. Membership uses no outcome information.
**Considered and rejected:** (B) weighting by expected volume: smoother, but harder to explain. (C) tuning directly on Big-60 MAE: the pool shifts with the settings, so it's noisy and slow and the most prone to overfitting.
**Pre-registered:** The pool definition, wide grid, forward-chaining and comparisons were fixed before results were seen (see the `scripts/exp_tuning_target.py` docstring).
**Result (OOS 2020–23):** OE v2 tuned this way beats the baseline on the Big-60 by −0.055 MAE (CI [−0.093, −0.014], p = 0.004). That's the **first significant Big-60 win**. Volume shrinkage still earns its place under this target (−0.011, significant). Big-60 bias: baseline +0.92 → +0.53. It's slightly worse on all players (+0.013), which is expected and acceptable because starters are what we're graded on.
**Scale, honestly:** 0.055 pts is about 0.8% of MAE. Weekly fantasy outcomes are mostly noise, so gains come in small, hard-won steps.

### 2026-11-01: Current model settings (OE v2, tuned on all of dev 2019–2023, relevant-player loss)
| Component | Volume half-life | Long-run half-life | m (vol. prior, games) | Efficiency half-life | k (eff. prior) |
|---|---|---|---|---|---|
| Receiving | 4 | 64 | 4 | 12 | 50 targets |
| Rushing | 1 | 16 | 2 | 6 | 100 carries |
| Passing | 6 | 16 | 2 | 6 | 100 attempts |
| Other (fumbles, return TDs) | — | — | — | 128 (≈ constant) | — |
**Reading them:** Rushing again needs the most efficiency shrinkage (k = 100 carries). Rushing volume reacts fastest (half-life 1, blended roughly 50/50 with a 16-game average), because backfield roles shift with injuries and game script. Receiving volume uses a longer anchor (64 games), because target roles are sticky.
**Sensitivity:** The error curves are flat near the optimum (k from 25 to 100 changes MSE by < 0.2%), so conclusions don't hinge on exact values. The settings vary across folds (e.g. receiving efficiency half-life 16–64), which is consistent with that flatness.
**Grid edges (logged, not chased):** Rushing hl_vol = 1 and "other" hl = 128 sit at grid edges. Both are natural limits ("about the last game" and "about a constant"). In the folds, receiving m = 8 was at the grid maximum. Testing m = 16 would be a separate, logged experiment.
**Forking-paths caution:** We have now tried several variants on dev seasons (v1, v2 narrow, v2 wide, option A). The 2024 validation season is the real check that this isn't an artefact of trying many things.

### 2026-11-01: Paper ablation: shrinkage is the source of the gain
**Setup:** All four models run in one forward-chained experiment (OOS 2020–23) with the same tuning target (relevant players), the same Big-60 union pool and the same bootstrap. See `paper/results_shrinkage_ablation.md`.
**Result (Big-60 MAE):** baseline 6.648, opp × eff without shrinkage 6.651, + efficiency shrinkage 6.597, + volume shrinkage 6.587 (current; −0.062 vs baseline, CI [−0.103, −0.019], p = 0.003).
**Step contributions:** Decomposition alone +0.003 (n.s.). Efficiency shrinkage −0.054 (p < 0.001). Volume shrinkage −0.011 (p = 0.013).
**Interpretation:** Splitting points into volume × efficiency doesn't help by itself, because it just divides the noise into two parts. The gain comes from treating each part with the right amount of skepticism (empirical Bayes). This is the paper's core methodological claim.
**Note:** The "v1" here is tuned on relevant players. The earlier v1 result (Big-60 −0.003, tuned on all players) used the old tuning target, and both stay logged.

### 2026-11-01: Team context (v3): rejected for now; v2 stays current
**Design (pre-registered):** Player volume = shrunk share of team volume (same short/long-run blend as volume) × the team's decayed historical average volume (half-life 4–64 team games, tuned). It uses the player's current team, so a traded player gets his new team's volume. Same framework as the paper ablation.
**Result (OOS 2020–23):** On the Big-60, v3 vs v2 is +0.009 (CI [−0.019, +0.035], p = 0.72): no gain. On all players it's −0.009 (significant), but that isn't our target.
**Why (interpretation):** A team's *historical* average volume adds almost nothing beyond a player's own volume history, which already reflects his team's volume. Team pass volume is also noisy and mean-reverting week to week (it depends on game script). The value of the share × team structure should come from **forward-looking** team volume: betting lines (implied points and spread → expected plays and pass rate) and teammate injuries (vacated share). Neither is in yet.
**Decision:** Keep v2 as the current model. Keep the team-context code as the base for betting-market and injury features, and re-test v3 when those arrive.
**Expectation was stated in advance:** Before running, we expected little gain on its own.

### 2026-11-01: Betting lines (v4): pre-registration (written before results)
**Source:** nflverse schedules `spread_line` (closing spread; + = home favoured) and `total_line` (closing over/under). Complete for all 2,127 regular-season games 2018–2025. Sanity checks: mean (actual margin − spread) = −0.07 and mean (actual total − line) = +0.57, so the lines are unbiased.
**Transformation:** implied team points = (total + own margin) / 2. Expected margin = +spread (home) / −spread (away).
**Look-ahead:** These are closing lines, known at kickoff. Our projections freeze at kickoff, so this is legitimate for backtests. **Live use** needs a pre-kickoff odds snapshot from a verified free/low-cost source (CLAUDE.md), to be chosen in Phase 3. Backtest results with closing lines may be slightly optimistic compared with lines captured hours before kickoff.
**Pre-check (dev only; fit 2019–21, scored 2022–23):** Lines raise the explained variance of team weekly volume from 9.1% → 11.2% (targets), 5.3% → 6.7% (carries) and 8.7% → 10.2% (attempts). The signs match football logic: favourites run more and pass less, and high totals produce more passes. About 90% of weekly team volume is unpredictable before kickoff.
**Model (v4):** Team context (v3) with team volume = OLS(history, implied points, margin), where the coefficients for season s are fitted on team-games from seasons < s only.
**Test plan:** Same framework as the paper ablation (relevant-player tuning, forward-chained OOS 2020–23, Big-60 union pool, paired week-clustered bootstrap). **Headline: v4 vs v2.** Secondary: v4 vs v3, v4 vs baseline. Using lines for efficiency (TD environment) is a **separate** later experiment, so only one feature is tested at a time.

### 2026-11-01: Betting lines: placebo reveals a confound; pre-registration of the clean ablation
**Real-lines result (OOS 2020–23, Big-60):** v4 vs v2 −0.066 [−0.101, −0.032]. v4 vs v3 −0.073. v4 vs baseline −0.117. Bias +0.32.
**Placebo (lines shuffled within season):** v4 vs v2 −0.017 (n.s.), but v4 vs v3 is still **−0.024 (p = 0.001)**, and bias +0.33.
**Interpretation:** This is not leakage: shuffled lines don't produce the big gain. But v4 bundled two changes: (1) a team-volume **regression** whose history coefficient (about 0.6) shrinks team volume toward the league average (team-level regression to the mean), and (2) the **information in the lines**. The placebo isolates (1).
**Pre-registered clean ablation (written before running):** Add v4-reg = the same walk-forward regression with history only (no lines). Compare, in one run with the same framework: **v4 vs v4-reg = value of betting lines** (headline), and v4-reg vs v2 = value of team-volume shrinkage. The placebo run stays logged.

### 2026-11-01: Betting lines: clean ablation result; v4 becomes the current model
**Result (OOS 2020–23, Big-60):** The betting-market information (v4 vs v4-reg) is −0.045 [−0.060, −0.031], p < 0.001. This was the pre-registered headline, and it passes. Team-volume shrinkage alone (v4-reg vs v2) is −0.022 (p = 0.07; significant on all players). Total v4 vs v2 is −0.068, and **v4 vs baseline is −0.119** (6.659 → 6.540).
**Mechanism:** The regression removes bias (Big-60 over-projection +0.47 → +0.33). The lines don't change bias (+0.33 with and without). Instead they improve *discrimination*: the market knows which teams will have high volume in that particular game.
**Decision:** **v4 is the current model.** v4-reg's team-volume shrinkage is kept inside v4, even though it isn't individually significant on the Big-60, because (a) the lines regression requires that structure, (b) it's significant on all players, and (c) it's the same empirical-Bayes logic used everywhere else.
**Final settings (all dev 2019–2023):** receiving 4/32/100/64/4 with team half-life 8; rushing 1/6/50/16/2, team 4; passing 3/8/200/64/2, team 16 (format: hl_vol/hl_eff/k/hl_long/m). Saved in `reports/opp_eff_params.json`.
**Paper:** `paper/results_betting_lines.md` (ablation, placebo, coefficients).
**Live-use requirement (Phase 3):** Pick and verify a pre-kickoff odds source (free/low-cost, terms of service respected) and snapshot lines with timestamps. Until then, the backtest uses nflverse closing lines.

### 2026-11-02: Betting lines for efficiency (v5): pre-registration (written before results)
**Idea (economics):** Implied team points measure the expected scoring environment. In a game the market expects to be high-scoring, each target, carry or pass attempt should be worth more (more touchdowns, more yards per play), on top of the extra *volume* that v4 already captures.
**Model (v5) = v4 with an efficiency multiplier per component c (rec, rush, pass):**
  eff_adj = eff × (1 + α_c + β_c · (implied − ī))
  ī is the league mean implied points in the training seasons. β_c is the % change in points per opportunity for each extra implied point. α_c is an overall calibration term.
**Fitting:** Walk-forward by season (same rule as v4's team regression). Coefficients for season s use only seasons < s. Least squares on actual component points against the model's own pre-game baseline (eff × actual opportunities), over every player-game with at least 1 opportunity. Settings (half-lives, k, m) are tuned exactly as in v4 and are **not** re-tuned with the multiplier. The multiplier is fitted afterwards.
**Control (lesson from the v4 placebo):** v5-cal = the same multiplier with α only (no lines), so a pure calibration effect can't be credited to the lines.
**Test plan:** Same framework (relevant-player tuning, forward-chained OOS 2020–23, Big-60 union pool, paired week-clustered bootstrap). **Headline: v5 vs v5-cal = value of lines for efficiency.** Adopt v5 only if this is significant (p < 0.05) *and* v5 beats v4. If only the calibration term helps, log it as a finding but don't adopt it here; it would need its own pre-registered test.
**Expectation:** Small. Touchdowns are noisy, and part of the scoring environment is already in v4's volume. A null result is plausible and will be logged.
**After this:** The model is frozen and the one-time 2024 validation is run (Parv approved, 2026-11-02).

### 2026-11-02: Betting lines for efficiency: result; v5 becomes the current model
**Result (OOS 2020–23, Big-60):** The pre-registered headline, v5 vs v5-cal (the value of lines for efficiency), is −0.052 [−0.071, −0.033], p < 0.001. v5 vs v4 is −0.072 (p < 0.001). Both adoption conditions are met. v5 vs baseline is −0.188 (6.666 → 6.477).
**Fitted environment effect (β), stable across folds:** Each extra implied team point raises points per opportunity by about +1.1% to +1.3% for receiving, +1.2% for rushing and +1.3% to +1.9% for passing. So a team implied for 28 instead of 21 gets roughly +8% to +13% more per opportunity, on top of v4's extra volume.
**Calibration term (α, a finding, not credited to the lines):** The control's multiplier is below 1, especially for passing (0.91 to 0.95). Shrunk efficiency still over-projects slightly, which is consistent with v4's leftover +0.30 bias. α only (v5-cal) gives −0.021 vs v4 and brings Big-60 bias to about 0. It stays inside v5 as pre-registered (v5 = α + β), but the paper credits the lines only with the −0.052.
**No re-tuning:** Settings stay as v4's. Final v5 = the v4 settings in `reports/opp_eff_params.json` with `eff_adj = "lines"`. The multiplier is refitted walk-forward each season.
**Forking-paths note:** This is the sixth model variant tried on 2019–2023. The 2024 validation below is the check against having overfit the dev seasons by choosing among variants.

### 2026-11-02: 2024 validation: pre-registration (written before running; Parv approved C)
**Frozen model:** v5 with `reports/opp_eff_params.json` (tuned 2019–23). The baseline method is tuned on 2019–23 (the pre-stated rule: lowest Big-60 MAE). Nothing is tuned on 2024. The run is one-time: `scripts/validate_2024.py` refuses to run a second time.
**Primary test:** Big-60 MAE (union of both models' own pools), v5 vs baseline, paired bootstrap clustered by week (18 clusters, so CIs will be wider than on dev). **Pass = diff < 0 with p < 0.05.**
**Expectation:** The gain should shrink compared with dev (−0.188), because of the winner's curse from choosing among variants. A gain of roughly −0.08 to −0.15 would be consistent with honest generalisation.
**Also reported:** All-players MAE, per position (descriptive), RMSE, Spearman, bias, and the weekly head-to-head record on the baseline's own pool (the CLAUDE.md Big-60 format) and on ours.
**Whatever happens:** The result is logged. If it fails, we don't tweak and re-test on 2024. Any new idea is developed on 2019–23 and goes straight to the 2025 test.

### 2026-11-02: 2024 validation: result (PASSED)
**Primary test (pre-registered):** Big-60 MAE v5 vs baseline: 6.349 vs 6.506, diff −0.158 [−0.265, −0.049], p = 0.002. **Pass.**
**Generalisation:** The dev out-of-sample gain was −0.188, and 2024 keeps about 85% of it. That's a modest winner's-curse shrinkage, at the low-shrinkage end of the range we expected (−0.08 to −0.15, slightly better).
**Secondary:** On all players −0.049 (p = 0.001). RMSE 8.04 vs 8.17. Spearman 0.354 vs 0.317. By position (descriptive): QB −0.25, WR −0.21, RB −0.12, TE −0.03 (n.s.). Head-to-head on the baseline's own Big-60: **15–3**. On our own Big-60: 11–7.
**Two observations, logged as hypotheses and NOT acted on with 2024 data:**
1. **Bias flipped:** v5 under-projects in 2024 (−0.37; on dev +0.08). The calibration term α is fitted on earlier seasons, and 2024 may simply have been a higher-scoring year for top players. Watch this in 2025. Recalibration is not tuned on 2024.
2. **Late-season weakness:** All of the model's losses came in weeks 13–18 (3 of 3 on the baseline pool, 6 of 7 on ours). This could be noise (18 weeks), or a real late-season effect (workload changes, injuries piling up, teams resting starters). CLAUDE.md already lists "late-season workload ramps" as a situational modifier. **The plan:** test a week-of-season effect on 2019–23 only, as a pre-registered feature. If adopted, it goes straight to the 2025 test, with no second look at 2024.
**2024 is now spent.** `scripts/validate_2024.py` refuses to re-run. Any further feature is judged on 2019–23 (out-of-sample), and the final arbiter is the one-time 2025 test.

### 2026-11-02: Week-of-season effect (v6): pre-registration (written before results)
**Motivation:** In the 2024 validation, all of the model's weekly losses came late in the season. (2024 is spent, so it is used only as the reason to ask the question, never as evidence.) **Economic story:** Late in the season, injuries pile up, coaches manage workloads, teams out of contention try young players, playoff teams rest starters in week 18, and cold weather cuts passing. A trailing-average model reacts to these with a lag. Early in the season, roles and depth charts are still settling. CLAUDE.md lists "week-of-season ramp" as a situational modifier.
**Phases (fixed in advance, not chosen from data):** early = weeks 1–4, mid = 5–12, late = 13–18.
**Model (v6):** projection × (1 + γ[position, phase]).
  The raw γ per cell = (Σ actual − Σ projection) / Σ projection, over fantasy-relevant player-games (the fixed baseline-defined top 15/30/30/15 pool, the same as the tuning target) from seasons 2019..s−1 only (walk-forward). The projections are v5's.
  **Empirical-Bayes shrinkage** toward the position's overall γ (normal–normal): the between-phase variance is τ² = max(0, var of the phase γs − mean squared standard error). Each phase's γ moves toward the position mean by the factor B = se² / (se² + τ²). B is reported for every cell.
**Control (v6-pos):** One γ per position, ignoring phase. v6 vs v6-pos isolates the week-of-season effect from a plain position-level recalibration.
**Test plan:** Same framework (relevant-player tuning, forward-chained OOS 2020–23, Big-60 union pool, paired week-clustered bootstrap). **Headline: v6 vs v6-pos.** Adopt only if p < 0.05 *and* v6 beats v5. Descriptive: error in weeks 13–18 only.
**Expectation:** Uncertain. v5 already has per-component calibration (α), and the late-season pattern may be noise. A null result is plausible and will be logged. If adopted, it goes straight to the 2025 test. 2024 is never re-run.

### 2026-11-02: Week-of-season effect: REJECTED; v5 stays current
**Result (OOS 2020–23, Big-60):** The pre-registered headline, v6 vs v6-pos, is **+0.007** [−0.000, +0.016]. It is worse, not better. v6 vs v5 is −0.004 (p = 0.37). The position-only control vs v5 is −0.011 (p = 0.086): not significant, not adopted. Weeks 13–18 only (descriptive): v6 is *worse* than v5 by +0.021.
**Why it failed:**
1. **v5 has no late-season over-projection to fix.** Its late-season Big-60 bias is −0.15 (slight under-projection), and early and mid are +0.29 and +0.17. Betting lines and short-memory volume already absorb most late-season changes (rested starters, injuries) because the market prices them.
2. **Fixing bias ≠ lowering MAE.** v6 cut late-season bias from −0.15 to +0.03, yet late-season MAE rose. Fantasy points are right-skewed (a few huge games), so MAE is minimised by the *median* outcome, not the mean. Nudging projections up toward the mean pushes them past the median for most players. This is an important lesson for every calibration step.
3. **Shrinkage behaved as designed.** For WR and RB, and QB in most folds, the phases were pure noise, and EB shrank them fully to the position mean (B ≈ 1). Only TE showed a consistent pattern (late +10 to 12% raw, B ≈ 0.15), and acting on it still hurt out-of-sample.
**What this says about 2024:** The late-season losses in the 2024 validation are most likely noise (18 weeks, small margins), not a missing feature.
**Logged as a failed feature** (rigor rule 3). It goes in the paper. The `situational.py` shrinkage machinery is kept for the next situational modifiers (Week 1, prime time, weather), which need the same partial pooling.

### 2026-11-02: Injury data added
**Source:** nflverse `load_injuries` (official weekly NFL injury reports: practice participation + game designation), 2018–2025, 45,337 rows, saved as `data/raw/injuries.parquet`. It is downloaded separately (`pull_injuries`), so the data behind earlier results is not re-downloaded or changed. Free; it is the documented nflverse source CLAUDE.md names.
**Audit (dev 2019–23, skill positions, 8,363 rows):**
  - Timing: the median report is final 51 hours before kickoff (the Friday report). 0.10% were modified after kickoff. **Rule:** entries modified after kickoff are ignored (no look-ahead).
  - What designations mean (share who then played): Out 0.1%, Doubtful 1.5%, Questionable 65%, practice-only listing 89%. Did-not-practise 20%, Limited 69%, Full 89%.
  - 1 duplicate player-week and 6 rows with no matching game (negligible; handled in code).

### 2026-11-02: Vacated opportunity (v7): pre-registration (written before results)
**Idea (economics):** Targets and carries are a fixed pie in the short run. When a teammate is ruled out, his slice goes to the players who remain. The model should raise their shares *before* their own history catches up.
**Who counts as absent (Friday information only):** Designated **Out or Doubtful** on the final pre-kickoff report (≈ 99% miss the game). Questionable players are *not* treated as absent here. Their uncertainty (35% miss) and the player's own reduced role when he does play are a separate, later feature. We deliberately do *not* use "did not play" or the 90-minute inactive list, because we haven't verified a live source for it yet.
**Absent player's vacated share:** His own shrunk share of team volume (same formula and settings as the model) as of his most recent game for that team, this season or last.
**Model (v7) = v5 with, for receiving and rushing:**
  share′ = share × (1 + λ_same · V_same + λ_other · V_other)
  V_same / V_other = total vacated share of absent teammates at the player's own position / at other positions. λ is "% growth in a player's share per unit of vacated share", so his gain is proportional to his existing role (the WR1 absorbs more than the WR4). λ is fitted walk-forward (seasons < s, least squares on actual volume, no intercept, so teams without absences are untouched). Settings are not re-tuned. Passing is excluded: a backup QB has no meaningful share history. QB changes are a separate later feature.
**Placebo (pre-registered, same run):** v7-placebo reassigns each team-week's absences to a random other team in the same week. It should give ≈ 0 gain. If it doesn't, something leaks.
**Test plan:** Same framework (relevant-player tuning, forward-chained OOS 2020–23, Big-60 union pool, paired week-clustered bootstrap). **Headline: v7 vs v5.** Adopt only if p < 0.05 and the placebo shows no significant gain. Descriptive: player-games with V > 0. **Expectation:** Positive but modest overall. Most player-weeks have no relevant absence, so the gain is concentrated in the affected games.

### 2026-11-02: Vacated opportunity (v7): REJECTED; v5 stays current
**Result (OOS 2020–23, Big-60):** The pre-registered headline, v7 vs v5, is **+0.005** [−0.005, +0.015]: no gain, so rejected. In the 41% of Big-60 player-games with an absent teammate it is +0.013 (n.s.).
**The reallocation itself is real and stable:** λ_same = +0.43 to +0.60 for receiving and +0.25 to +0.46 for rushing in every fold. The placebo λ_same ≈ 0, as it should be. So when a WR with a 20% target share is ruled out, a teammate WR's share grows about 10% (0.5 × 0.20), proportional to his role. About half of the vacated share goes to existing same-position players; the rest goes to replacements and other positions. These are good numbers for the paper and the website's explanations, even though they don't lower error.
**Why it doesn't lower error (interpretation):**
1. **Mean vs median again** (as with v6). λ is fitted by least squares, so it targets the *mean*. Big-60 projections were already slightly high (bias +0.08), and v7 raises them further (+0.14). Fantasy points are right-skewed, so MAE rewards the *median*.
2. **Most of the information is already in the model.** Multi-week absences are already absorbed by the short volume half-lives (1 to 4 games), and betting lines move on injury news.
**The placebo "helped" (−0.009, p = 0.011). This is not leakage.** The shuffled absences come from other teams, so they carry no information about these games. But the placebo fit negative λs (−0.24 to −0.33 for other positions), which lowers projections for a random ~40% of players. That acts as a crude downward recalibration, consistent with point 1. It is the same lesson as the v4 placebo: an added regression structure can "work" through calibration, not information. That's why placebo controls are run every time.
**Systemic lesson, now seen twice (v6 and v7):** Our calibration steps fit means (least squares), but the model is graded on MAE. A possible pre-registered experiment is to fit calibration steps by least absolute deviations (median regression). That would be a *loss-alignment* change to the whole model, not a new feature. It needs its own pre-registration because of forking paths.
**Kept:** The injury data pipeline (`injuries.py`, timing rule, links) is kept for the next uses: the player's own Questionable/practice status, QB changes, and live projections.

### 2026-11-02: Loss alignment: median calibration (v8): pre-registration (written before results)
**Problem:** The model is built from averages: volume × efficiency, with least-squares fits. That makes it an estimate of the player's *mean* score. The Big-60 grades MAE, and MAE is minimised by the *median*. Fantasy points are right-skewed (big games pull the mean above the typical outcome), so a perfect mean forecast is systematically too high for MAE. Both rejected features (v6, v7) failed partly for this reason.
**Change (one step, at the end of the model):** v8 = v5 followed by a per-position linear map from the mean projection to the median outcome:
  median_proj = a_pos + b_pos · proj_v5
  This is fitted by **least absolute deviations** (median / quantile regression, τ = 0.5), walk-forward: for season s, it uses fantasy-relevant player-games (the fixed baseline-defined pool) from seasons 2019..s−1. Each fit uses thousands of player-games per position, so no shrinkage is needed (rule 2 is about small samples). The fitted a and b are reported every season.
  The model stays a mean model inside, so explanations ("baseline → adjustments") stay additive, and the final step converts mean → median. Since b > 0, the ranking *within* a position is unchanged, so the Big-60 pools and Spearman don't change. Only levels do.
**Control (v8-ols):** The same map fitted by least squares (mean-targeting recalibration). It separates *loss alignment* from plain *recalibration*.
**Decision rules:**
  - Adopt v8 if v8 vs v5 on the Big-60 is p < 0.05.
  - The mechanism claim ("median targeting is what helps") requires v8 vs v8-ols p < 0.05 *and* v8-ols to win on RMSE. Squared error is minimised by the mean, so each version should win its own loss.
**Pre-specified follow-ups, only if v8 is adopted:** (1) Re-test vacated opportunity (v7) once on top of v8. It is the rejected feature that showed real, stable signal. Only this one is re-tested, which limits forking paths. (2) Use the same quantile regression with τ = 0.1 / 0.9 for floor and ceiling (CLAUDE.md model step 4).
**Expectation:** A small but significant gain, mainly by lowering projections for high-variance players.

### 2026-11-02: Median calibration (v8): result; ADOPTED; mechanism only partly confirmed; fringe-player issue
**Adoption rule:** v8 vs v5 on the Big-60 is −0.054 [−0.097, −0.012], p = 0.006. **Met, so v8 is the current model.** v8 vs baseline (dev OOS) is −0.249.
**Mechanism rule (needs both):** (a) v8 vs v8-ols −0.029, p = 0.064: **not met**. (b) v8-ols wins RMSE (8.232 vs 8.307): **met**. So the honest claim is: *calibrating the final projection helps (both versions do), each version wins its own loss as theory predicts, and median targeting is directionally better for MAE but not significantly so on its own.* The paper reports exactly that, not "median targeting is the source of the gain."
**What the map does:** It barely changes QBs. RBs drop by about 1.8 to 2.2 points flat (b ≈ 1.0, a ≈ −2), and WRs and TEs by about 7 to 10% (a 15-point projection becomes 13.6 to 14.2). The median error of the Big-60 goes from +0.88 (v5: half of top players score at least 0.9 below projection) to −0.15. The mean bias goes to −0.97, which is exactly what a median forecast of a right-skewed outcome should do.
**Issue found (not hidden):** On all players, v8 is *worse* than v5 (+0.029), and v8-ols much worse (+0.403). The map is fitted on fantasy-relevant players only, and its intercept (for example the OLS WR a = +3.8) is applied to fringe players far below that range. That is extrapolation outside the fitted range. It barely matters for the Big-60 (top players), but the website shows every player. **Not fixed yet:** the possible fixes (fit on all players; apply only within the fitted range; a multiplicative-only map) are *new variants*, so they need Parv's choice and their own pre-registration.
**Pre-specified follow-ups (now triggered):** re-test v7 on top of v8, and floor/ceiling via τ = 0.1 / 0.9. Both are on hold until the fringe-player issue is decided, because both would build on the map.

### 2026-11-02: Percentage-only median calibration (v8m): pre-registration (Parv chose this fix; written before results)
**Change from v8:** Drop the intercept. median_proj = b_pos · proj_v5, fitted by least absolute deviations on the same rows (fantasy-relevant player-games, seasons 2019..s−1, walk-forward). Reading it: "a player's typical score is b% of his average projection". A 0 projection stays 0, so nothing is added to fringe players. This is one number per position.
**Decision rules:**
  1. **Primary:** v8m vs v5 on the Big-60, p < 0.05.
  2. **Safety (the reason for the change):** on all players, v8m must not be significantly worse than v5 (the 95% CI upper bound of v8m − v5 must be ≥ 0, or the difference ≤ 0).
  3. **Replace v8** if both hold. v8m vs v8 on the Big-60 is reported. We accept v8m even if it's slightly worse there, as long as it's not significantly worse (p(v8m better) > 0.05 against it, i.e. the CI includes 0 or favours v8m). Simplicity and safety for every displayed player outweigh a non-significant difference.
  If rule 2 fails, v8 stays and the issue stays open.

### 2026-11-02: v8m: result; ADOPTED, replaces v8
**Rule 1:** v8m vs v5 on the Big-60 is −0.054 [−0.099, −0.011], p = 0.007. ✅
**Rule 2 (safety):** On all players, v8m vs v5 is **−0.067** [−0.078, −0.058]. It is now *better* on fringe players too (v8 was +0.029). ✅
**Rule 3:** v8m vs v8 on the Big-60 is +0.000 [−0.009, +0.009]. Identical on top players. ✅ **v8m is the current model.**
**The fitted percentages are very stable across folds** (typical score as % of the mean projection): QB 102–104%, RB 85–87%, WR 92–96%, TE 91–92%. Interpretation: RB scoring is the most right-skewed (long TD runs, boom-or-bust usage), so the median RB week is well below his average. QB scoring is the least skewed (steady passing yards), and the slight >100% means QB projections ran a touch low. These four numbers are easy to defend and to show on the website.
**Big-60 median error** is −0.14 (v5 +0.88). The mean bias is −0.96, as expected for a median forecast.
**Frozen:** `reports/opp_eff_params.json` gains `"final_calibration": "lad_mult"`. The map itself is refitted walk-forward each season (seasons 2019..s−1, fantasy-relevant player-games).
**Next (pre-specified 2026-11-02):** (1) Re-test vacated opportunity (v7) once on top of v8m. (2) Floor/ceiling with τ = 0.1 / 0.9.

### 2026-11-02: Vacated opportunity on top of v8m (v7m): rules for the one pre-specified re-test (written before results)
**Model:** v7m = v5 + vacated opportunity (exactly as v7), then the v8m percentage map fitted on v7's own projections. **Placebo:** the same with absences moved to random teams (as before).
**Adopt only if:** v7m vs v8m on the Big-60 has p < 0.05, *and* the placebo vs v8m is not significantly better (p > 0.05), *and* v7m vs the placebo has p < 0.05. This is the last test of this feature on dev seasons. It won't be retried again.

### 2026-11-02: Vacated opportunity re-test (v7m): REJECTED (final for dev seasons)
**Result (Big-60):** v7m vs v8m is −0.002 [−0.012, +0.008], p = 0.35. v7m vs placebo is −0.005 (p = 0.19). Rule 1 fails, so the feature is rejected. It is not retried on dev seasons again.
**The placebo now gives nothing** (+0.003 vs v8m, where v7's placebo gave −0.009). This confirms the earlier reading: v7's placebo "gain" was a crude downward recalibration, and the median map now does that job properly.
**Conclusion for the paper:** Teammate absences shift shares in a real and stable way (λ_same ≈ 0.5), but the information is already in the model by kickoff. Short volume half-lives absorb multi-week absences, and betting lines price injury news. The loss mismatch was only part of the earlier failure. Injury data stays in the pipeline for live use and for the player's own status (a separate, later feature).

### 2026-11-02: Floor / ceiling, simple version (v9): pre-registration (written before results)
**Goal (CLAUDE.md model step 4):** Show a 10th / 50th / 90th percentile per player (floor / median / ceiling). About 80% of outcomes should land between floor and ceiling, and about 10% beyond each end.
**Model (v9):** floor = b10_pos × proj_v5, ceiling = b90_pos × proj_v5 (the median is already v8m = b50_pos × proj_v5). It uses the same quantile regression through the origin (τ = 0.1, 0.9), walk-forward on fantasy-relevant player-games from seasons 2019..s−1. Each position gets one floor percentage and one ceiling percentage. Every player at a position gets the same *proportional* range. A player-specific spread is the next, separate feature.
**Metrics:**
  - **Coverage** = share of outcomes inside [floor, ceiling]; tails = share below the floor or above the ceiling.
  - **Interval score** (Gneiting & Raftery, a proper scoring rule, lower is better): IS = (ceiling − floor) + (2/0.2)·(floor − y)·1[y < floor] + (2/0.2)·(y − ceiling)·1[y > ceiling]. It rewards narrow intervals and penalises misses, so you can't win by just widening.
**Benchmark:** The same method applied to the baseline projection (floor/ceiling = position quantile ratios × baseline). This tests whether our better centre gives better ranges.
**Pass criteria (Big-60 union, OOS 2020–23):**
  1. Coverage within 77–83%, and each tail within 7–13%.
  2. Interval score of v9 < benchmark, paired week-clustered bootstrap, p < 0.05.
**Diagnostics (descriptive only, not pass/fail):** Coverage by position, and by the player's pre-game volatility tercile. Volatility = coefficient of variation of his previous 16 games, which uses past data only. If high-volatility players are under-covered and steady players over-covered, that motivates the per-player-spread feature.

### 2026-11-02: Floor / ceiling (v9): result; ADOPTED for top players; fringe-player coverage problem
**Criterion 1 (calibration, Big-60):** 80.8% inside, 9.6% below the floor, 9.5% above the ceiling. ✅ (Per position: QB 81.4, RB 79.4, WR 82.0, TE 80.7.)
**Criterion 2 (accuracy):** Interval score 28.515 vs 28.946 for the benchmark, −0.431 [−0.659, −0.211], p < 0.001. ✅ The better centre makes the ranges better too. The benchmark is about equally well calibrated (81.0%), so the gain comes from being centred more accurately, not from having the right width.
**Fitted percentages (stable across folds):** floor / median / ceiling as % of the mean projection: QB 48–51 / 101–104 / 159–165; RB 30–35 / 85–87 / 167–172; WR 31–32 / 92–96 / 182–188; TE 25–26 / 91–92 / 180–203. TEs have the widest relative range (touchdown-dependent), QBs the narrowest.
**Honest scale:** For a typical Big-60 player the median is 14.1, the floor 5.2 and the ceiling 26.7. A width of about 21 points is the true week-to-week uncertainty.
**Diagnostic, volatility terciles (descriptive):** steady 81.4%, middle 83.4%, volatile 78.2%, no history 74.7%. The pattern is mild: volatile players are slightly under-covered. This is modest evidence for the per-player spread feature, which is now justified but should be expected to give only a small gain.
**Problem (not a pass criterion, but it blocks website use):** On **all players**, coverage is only 51.4%, with 32.0% below the floor. Fringe and backup players often score near 0 (zero-snap and garbage-time weeks), so a floor at 30% of the projection is far too high for them. The percentages were fitted on fantasy-relevant players only. **Status:** v9 is adopted for the Big-60 / top players. The website must not show v9 floors for fringe players until this is fixed. The fix (e.g. letting the floor and ceiling depend on projection level or role) should be designed together with the per-player-spread feature and pre-registered.

### 2026-11-02: Floor / ceiling for all players + per-player spread (v10): pre-registration (written before results)
**Problems being fixed:** (1) v9 floors are far too high for fringe players: 51% all-player coverage. (2) Volatile players are mildly under-covered (78% vs 81–83%).
**Model:** For each position and τ ∈ {0.1, 0.9}, a quantile regression fitted on **all** player-games (not only relevant ones), walk-forward on seasons 2019..s−1:
  q_τ = a_τ + b_τ · proj + c_τ · proj · z
  - proj = the v5 mean projection.
  - The intercept a lets low projections get a floor near 0 (which fixes fringe players).
  - z = the player's **shrunk volatility** minus the position average. Volatility = coefficient of variation of his previous ≤ 16 games, shrunk toward the position's average CV with weight n/(n + 8) (n = games available; prior strength 8 is fixed in advance, not tuned). Players with < 2 games get z = 0. This uses pre-game data only. c is "how much wider the range gets for a more volatile player, in proportion to his projection".
  - The median stays v8m (the point projection doesn't change here).
  - If quantiles cross, floor = min(floor, median) and ceiling = max(ceiling, median).
**Control (v10-novol):** The same without the z term (c = 0). It separates the per-player spread from the projection-level fix.
**Pass criteria (OOS 2020–23):**
  1. Calibration on **both** the Big-60 and all players: 77–83% inside, each tail 7–13%.
  2. Interval score vs v9: all players better (p < 0.05). Big-60 not significantly worse (p(v10 worse) ≥ 0.05).
  3. Per-player spread: v10 vs v10-novol interval score on the Big-60, p < 0.05. If 1–2 pass but 3 fails, adopt v10-novol.
**Diagnostics:** Coverage by position, by volatility tercile and by projection decile (all players).

### 2026-11-02: v10 floor/ceiling: result; ADOPTED (with per-player spread)
**Criterion 1 (calibration in both pools):** Big-60 82.5% inside (7.2% below, 10.3% above). All players 79.0% (11.5% / 9.5%). Both are within the 77–83% and 7–13% bands. ✅ Every position is 78.6–79.5% on all players (v9 was 44–61%).
**Criterion 2:** Interval score vs v9: all players −2.193 (p < 0.001) ✅. Big-60 −0.029 [−0.199, +0.134], not worse ✅.
**Criterion 3 (per-player spread):** v10 vs v10-novol on the Big-60 is −0.426 [−0.559, −0.304], p < 0.001 ✅. Without volatility, top-player ranges are too wide (85.3%, only 5.6% below the floor), because fitting on all players inflates the spread. Volatility lets steady stars get narrow ranges and boom-or-bust players wide ones. Volatility terciles on the Big-60 under v10: 82.4 / 82.1 / 83.0%, so calibration is now even across player types.
**Reading the coefficients (2023 fold):** For volatility, c is negative for floors and positive for ceilings at every position. A more volatile player gets a lower floor *and* a higher ceiling, as expected. Example: an RB with volatility +0.3 above average gets his ceiling raised by about 0.29 × projection.
**Remaining weakness (logged, not fixed):** Conditional calibration by projection decile is uneven. The lowest projections are over-covered (D1 92%, D2 85%), and the middle-low ones (projections 3–6 points, D4–D6) are under-covered at 71–73%, with 16–20% below the floor. Those players' outcomes are bimodal: a near-zero week (no role that game) or a normal one. A linear quantile map can't bend to that. It barely affects fantasy-relevant players (D9–D10 82%). A future fix could model "plays a real role this week" separately (two-part / hurdle model). That is out of scope now.
**Current model:** median = v8m; floor/ceiling = v10. Settings recorded in `reports/opp_eff_params.json`.

### 2026-11-02: One prediction function + explanation waterfall (CLAUDE.md model step 5)
**Decision:** All projections now come from one function, `predict.predict()`. It reads the frozen model from `reports/opp_eff_params.json` and returns, for every player-game, the median, floor and ceiling plus a step-by-step explanation. The website, the in-season pipeline and the final 2025 test will all call this same function, so the number we publish is the number we grade.
**Frozen baseline:** `baseline_method = ewma_hl8` is now written into the settings file instead of being re-tuned on every run. It is what tuning on 2019–2023 picked and what the 2024 validation used.
**Explanation method: a sequential waterfall.** It starts from the baseline (recent average). Each step switches on one more piece of the model, with every frozen setting held fixed, and the step's value is how much the projection changes. The steps:
  1. role & efficiency (own history)
  2. team context
  3. betting lines: team volume
  4. efficiency calibration (α only)
  5. betting lines: scoring environment
  6. median adjustment

The steps add up exactly to the median (checked to 1e-15).
**Why the order matters, and why this order:** A sequential breakdown depends on the order of the steps (a known limitation). We use the order in which each piece was adopted, which is also the order in which each was tested (each against the model before it). So every step answers the same question its experiment answered. Shapley values give an order-free alternative by averaging over all 720 orders, but they cost 720× more to compute and are harder to explain on a website. We don't use them now; they could be a robustness appendix in the paper.
**Why efficiency calibration is a separate step:** The scoring-environment multiplier is 1 + α + β·(implied − ī). α is a general correction with no game information; only β uses the betting market. Splitting them, the same way as the pre-registered v5-cal control, keeps the "betting lines" step from taking credit for the general correction.
**Not a feature, so nothing to earn:** This changes no projection. The mean projection is identical to the frozen v5 model validated on 2024 (checked), and the median, floor and ceiling are v8m / v10 as adopted.
**Safeguards:**
  - 2025 rows are dropped unless `allow_test=True`, which only the final-test script will pass.
  - The settings loader refuses any setting the code doesn't implement, and refuses switching on the rejected vacated-opportunity feature.
  - No-look-ahead check on real data: 2023 week 10 projections are identical (difference 0.0) with or without every later game in the data.
**Known limits:**
  - Shrinkage is reported per component (rigor rule 2): how much each player's efficiency is pulled to the league average.
  - About 4% of player-games (first career games) have no history, so they get no projection or explanation.
  - Floor and ceiling start in 2020, because the bands need a season of earlier data.
  - Live use needs a row for each upcoming game (team, opponent, betting line) before stats exist. That belongs to the Phase 3/4 pipeline.

### 2026-11-02: Week 1 effect (v11): pre-registration (written before results)
**Economic story:** A Week 1 projection is built almost entirely from *last season's* games. In between come the offseason: new teammates and coordinators, rookies, holdouts, players recovering from injury and players who simply aged. Every player's information is therefore stale in the same way. Teams also manage veteran workloads in the opener, after a preseason in which starters barely play. If Week 1 outcomes differ systematically from what the model expects (for example, lower or more spread-out scoring), a Week 1 adjustment captures it. CLAUDE.md lists "Week 1 efficiency" as a core situational effect, with player-specific effects partially pooled.
**What is adjusted:** The **median** (v8m), not the mean. The week-of-season test showed that shifting the mean toward actual scores raises MAE, because the scores are skewed. So every Week 1 effect is estimated with the same median-targeting (least absolute deviations) method as v8m.
**Model v11 (position level):** For Week 1 rows, median_w1 = median × (1 + γ_pos).
  - The raw γ_pos is fitted by LAD through the origin (actual ≈ (1 + γ)·median) on Week 1 fantasy-relevant player-games, seasons 2019..s−1 (walk-forward).
  - Its standard error se_pos comes from a bootstrap that resamples whole games (200 draws, fixed seed).
  - **Empirical-Bayes shrinkage toward 0** ("no Week 1 effect", since v8m is already calibrated over all weeks): τ² = max(0, mean(γ_pos²) − mean(se_pos²)) across the four positions, B_pos = se² / (se² + τ²), γ = (1 − B)·raw.
**Model v11p (player level, on top of v11):** γ_i = γ_pos + (1 − B_i)·ū_i.
  - ū_i = the player's average Week 1 residual ratio (actual/median_w1 − 1) over his earlier Week 1s (n_i ≤ 3 in dev).
  - B_i = (σ²/n_i) / (σ²/n_i + τ_p²). σ² is the pooled within-player variance, and τ_p² = max(0, var(ū_i) − mean(σ²/n_i)) across players at that position. Players with no earlier Week 1 get γ_pos.
  - The average B_i is reported, as rigor rule 2 requires.
**Test (OOS 2020–23, Week 1 games only):** The model is re-tuned per fold as in every experiment.
  - Pools: the Big-60 union (base / v8m / v11 / v11p) and all players.
  - **Paired bootstrap clustered by game** (only 4 Week 1s exist, so week clusters are impossible).
**Headline:** v11 vs v8m on Big-60 Week 1. Adopt v11 only if p < 0.05. Adopt v11p only if v11p vs v11 also has p < 0.05.
**Diagnostics (descriptive):**
  - v8m's Week 1 bias, and its share of outcomes above the median, by position.
  - Floor/ceiling (v10) coverage in Week 1.
**Honest power warning:** Only about 250 Big-60 player-games are available (4 seasons × ~62). An effect that cut Week 1 MAE by 0.2 points might still not reach p < 0.05, and a true Week 1 effect moves the season-wide MAE by only 1/18 of its size. A null result here would mean "not detectable with 4 openers", not "proved absent". The player-level effect, with at most 3 earlier openers per player, is expected to shrink almost entirely to the position effect (B_i ≈ 1). Logging that is itself the point of rule 2.

### 2026-11-02: Week 1 effect: result; NOT ADOPTED (position level); player level REJECTED
**Headline (pre-registered): v11 vs v8m, Big-60 Week 1, OOS 2020–23:** −0.053 points [−0.192, +0.084], p = 0.21. The point estimate favours v11, but it is not significant. **Not adopted.** v8m stays current.
**The pattern is real-looking, but there are only four openers to test it on:**
  - **Every fold** estimated a negative Week 1 effect for RBs (−10 to −22% raw) and TEs (−20 to −32% raw).
  - The diagnostic agrees. In Week 1, only 42% of top players score above their v8m median, against 51% in other weeks. For TEs it is 34% (vs 52%), for RBs 41% (vs 53%).
  - The median projection is too high by +1.25 points in Week 1. Plausible reasons: stale offseason information, vets' workloads managed in the opener, and new roles not yet settled.
  - Shrinkage (B = 0.1 to 0.6) roughly halved those raw effects, so v11 moved the right way: Big-60 TE Week 1 MAE fell 5.28 → 4.91.
  - On all players the gain is significant: −0.043, p = 0.006.
**Why we still don't adopt it:**
  1. The adoption rule was fixed in advance: the Big-60 headline with p < 0.05. Adopting on the secondary pool after seeing the results would be a forking-paths choice. This is the same discipline that made us reject things before.
  2. As the power warning predicted, 287 player-games across 4 openers can't separate a 0.05-point gain from noise. Even if the effect is real, it changes the season-wide MAE by about 0.003.
**Player-specific Week 1 effects (v11p): rejected, and worse** (+0.167, p > 0.99).
  - With at most 3 earlier openers per player, partial pooling trusted the player's own history for RBs (average B 0.62–0.85).
  - It then chased noise: one opener is one game.
  - This is the rule-2 lesson in its clearest form. Even shrunk, a player effect estimated from 1–3 games hurts. Week 1 deviations are not a stable player trait in this data.
**Floor/ceiling in Week 1:** Coverage is 82.6% vs 82.5% in other weeks, so the ranges need no Week 1 fix.
**Logged as a failed feature** (rigor rule 3). It is a candidate to **re-test once more openers exist** (2026+ live seasons), pre-registered the same way. It must not be re-tested on 2024 (spent) or 2025 (test).

### 2026-11-02: Prime-time effect (v12): pre-registration (written before results)
**Definition (fixed in advance, from the schedule only):** A game is prime time if its scheduled kickoff (nflverse `gametime`, US Eastern) is at **19:00 or later**. That covers Sunday, Monday, Thursday and Saturday night games. Thanksgiving/Christmas afternoon games, London morning games and Sunday 1 pm / 4 pm games are not prime time. The flag is known well before kickoff, so there is no look-ahead.
**Economic story:**
  - Prime-time games are stand-alone national games. Defenses get extra preparation for featured opponents.
  - Thursday games come on short rest.
  - Betting folklore says prime-time games go "under".
**The key question:** Our model already uses the betting total for every game, so a league-wide prime-time scoring effect should already be priced in. The question is whether players' points *still* differ in prime time after the market's line. CLAUDE.md lists "prime-time splits" as a core situational effect, including player-specific ones.
**Model v12 (position level):** For prime-time rows, median × (1 + γ_pos). γ_pos is fitted by LAD through the origin on prime-time fantasy-relevant player-games from seasons 2019..s−1 (walk-forward), with the standard error from a bootstrap over games. It is EB-shrunk toward 0 across positions, with exactly the Week 1 machinery: τ² = max(0, mean(γ²) − mean(se²)), B = se²/(se² + τ²).
**Model v12p (player level, on top of v12):** "Prime-time players". The player's average prime-time residual ratio over his earlier prime-time games is partially pooled toward the position effect (normal–normal, B_i reported), as in v11p.
**Placebo (v12-placebo):** The same as v12, but the "prime-time" label goes to randomly chosen games: in each week, the same number of games as truly were prime time, with a fixed seed. If the placebo also "helps", the gain comes from the procedure (for example, a general recalibration), not from prime time.
**Test (OOS 2020–23):** Re-tuned per fold as in every experiment.
  - Pool: the Big-60 union, **restricted to prime-time player-games**. The paired bootstrap is clustered by season-week, which is possible here because prime time occurs every week (about 72 clusters).
  - **Headline: v12 vs v8m on Big-60 prime-time rows. Adopt v12 only if p < 0.05 and v12 beats v12-placebo** (on that placebo's own prime-time rows: the placebo is judged on the rows it modifies).
  - Adopt v12p only if v12p vs v12 also has p < 0.05.
  - Secondary: all players on prime-time rows, and the full-season Big-60 (v12 changes only prime-time rows).
**Diagnostics (descriptive):** v8m's share above the median and its median error in prime time vs other games, by position, and by slot (Thursday / Sunday night / Monday / Saturday). Also floor/ceiling coverage in prime time.
**Power:** About 15% of games are prime time, so expect roughly 700–800 Big-60 prime-time player-games, about three times the Week 1 sample. A 0.1-point effect is still marginal to detect.
**Expectation:** Most likely a null. The betting total already carries prime-time scoring levels, and v5 converts implied points into both volume and efficiency. Player-level prime-time "splits" are a classic small-sample narrative, and they are expected to shrink to ~nothing (B_i ≈ 1).

### 2026-11-02: Prime-time effect: result; REJECTED (position and player level). A fitting bug found by the placebo
**Headline (pre-registered): v12 vs v8m, Big-60 prime-time player-games (n = 1,125), OOS 2020–23:** +0.028 [−0.022, +0.082]. It is worse. **Rejected.** Player-level prime-time splits (v12p) vs v12: +0.021, rejected. On all players, prime-time rows: −0.023 (p = 0.001). That is secondary and does not override the rule.
**There is nothing to fix:**
  - In prime time, 50.2% of top players score above their v8m median, against 50.8% in other games, and floor/ceiling coverage is 82.6% vs 82.3%.
  - This is exactly what the expectation said. The betting total already prices the prime-time scoring level, and v5 converts it into volume and efficiency.
  - Slot differences (Sunday night 45.6% above the median, Thursday 54.7%) are descriptive only. They point in opposite directions and were not tested.
**Bug found by the placebo:**
  - **What happened:** The placebo (prime-time labels on random games) fitted γ just as negative as the real flag (RB −18.5%, WR −9.9% in 2020). Random games should have no effect, so the fitting procedure itself had a problem.
  - **The bug:** The situation effects were fitted on the v8m median of earlier seasons *starting in 2019*. But in 2019 the median calibration has no earlier season to learn from, so the 2019 "median" is the uncalibrated mean projection.
  - **The size of it:** Checked with the frozen model, 2019's fit rows are over-projected by RB −13%, WR −7%, TE −8%, against roughly ±5% with no consistent sign in 2020–22.
  - **Effect on the estimates:** Every situation γ was pulled negative. The pull is largest in early folds, where 2019 is all or half of the fit data.
**Effect on the Week 1 result (correction to the entry above):**
  - The claim that "every fold estimated a negative Week 1 effect for RBs/TEs" is **partly an artifact** of this bug. The 2020 fold was fitted on 2019 alone.
  - The **diagnostic still stands**: in OOS 2020–23 Week 1 games, 42% of top players scored above their correctly calibrated median, vs 51% in other weeks. That is evidence of a real Week 1 over-projection.
  - The v11 test itself (not adopted, p = 0.21) was run with the contaminated estimator, so it is not a clean test of the idea.
**Fix (not yet applied, pending Parv's decision):** Fit situation effects only on seasons whose median was itself calibrated, i.e. seasons ≥ 2020 (first_season = 2020). The earlier v6 week-of-season test fitted on the mean projection (v5), not the median, so it was not affected. **Open question:** should Week 1 be re-run once with the fixed estimator and exactly the same pre-registered rule, clearly labelled as a bug-fix re-run? Prime time doesn't need a re-run: the diagnostic shows no prime-time deviation to capture.

### 2026-11-02: Week 1 effect: bug-fix re-run, pre-registration (written before results; the final test of this idea on dev data)
**Parv's decision:** Re-run Week 1 once with the fitting bug fixed. If it fails, the Week 1 idea is closed on development data. It may be revisited only on future live seasons (2026+) under a new pre-registration.
**The only change:** Situation effects are fitted on seasons ≥ **2020**, the first season whose median was itself calibrated (it was 2019). That is all. The models (v11, v11p), the EB shrinkage, the bootstrap, the pool (Big-60 union, Week 1, **OOS 2020–23**), the game-clustered test and the adoption rules (v11 vs v8m p < 0.05; v11p also needs p < 0.05 vs v11) are **identical** to the original pre-registration.
**Known consequence, stated in advance:** The 2020 fold now has no earlier calibrated Week 1, so v11 = v8m in 2020. Those rows add zero difference and dilute the headline. We still keep 2020–23 as the headline pool, because changing the pool after seeing results would be a second fork. The 2021–23 rows are reported as descriptive only. The fit data is also smaller (one to three openers), so power is lower than in the first run.
**Reproducibility:** The first run's scripts keep first_season = 2019 explicitly, so the committed reports still regenerate exactly. The re-run writes `reports/exp_week1_fixed.md`.

### 2026-11-02: Week 1 effect, bug-fix re-run: result; NOT ADOPTED. Week 1 closed on development data
**Headline (same pre-registered rule): v11 vs v8m, Big-60 Week 1, OOS 2020–23:** −0.010 [−0.039, +0.017], p = 0.22. **Not adopted.** On 2021–23 only (descriptive), −0.014, p = 0.24. Player-level (v11p) vs v11: +0.054 (worse); rejected again.
**What the fix changed:**
  - With 2019's uncalibrated rows gone, the raw position effects are smaller and less consistent. RB −4 to −7% (was −10 to −22%). QB now *positive* (+8 to +9%). TE stays the most negative (−14 to −35%), but its standard errors are 10–19%.
  - The between-position spread is no bigger than the noise, so τ² drops toward 0. By the 2023 fold (τ² = 0), EB shrinks every position fully to "no Week 1 effect" (B = 1.00).
  - **The shrinkage is doing exactly its job:** with 1–3 calibrated openers to learn from, the data cannot tell a Week 1 effect apart from noise.
**Reconciling with the diagnostic:** OOS, only 42% of top players beat their median in Week 1 (vs 51% in other weeks), and TEs 34%. That is a descriptive pattern on 283 player-games. It could be real (stale offseason information) or partly chance. Our estimator, which must learn it from *earlier* openers only, could not exploit it reliably. That is the honest summary: **possible signal, not usable with four seasons of openers.**
**Verdict:** The Week 1 idea is **closed on development data**, as pre-registered. Re-testing is allowed only on future live seasons (2026+), under a new pre-registration. The fixed estimator (`FIRST_CALIBRATED_SEASON = 2020`) is now the default for all future situation tests (weather next). The original first run's report regenerates identically (only its title was relabelled "first run").

### 2026-11-02: Weather effect (v13): pre-registration (written before results)
**Parv's decision:** Use the weather already in the nflverse schedules (option A). No new download. Switch to a full weather source (e.g. Open-Meteo, terms checked first) only if this finds a signal worth chasing, or when the live pipeline is built.
**Data limits, disclosed in advance:**
  - nflverse has temperature and wind only. **There is no rain/snow field**, so precipitation is not tested.
  - The values are observed at kickoff, not forecasts. Live use will rely on forecasts a few hours out, so the backtest is slightly optimistic.
  - Temperature/wind are missing for 91 of 187 outdoor games in 2022 and 41 of 191 in 2023 (very few in other seasons).
**Definition (fixed in advance):** A game is **bad weather** if the roof is `outdoors` or `open` AND (wind ≥ **15 mph** OR temperature ≤ **32°F**). Domes and closed roofs are never flagged.
  - **Missing-data rule:** an outdoor game with missing temperature/wind is treated as **not flagged**. Some real bad-weather games are therefore mislabelled as normal, which biases any effect toward zero. The number of such games is reported.
  - In 2019–23, 134 of 933 outdoor games (14.4%) qualify.
**Economic story:** Wind and cold make passing and kicking harder. But the betting total already reacts strongly to forecast wind, and our model uses that total for both volume and efficiency. So the question is whether players still miss their median in bad weather *after* the market's line. The plausible residual is a **reallocation**: teams run more and throw less, so pass catchers and QBs fall short (negative γ) while RBs hold up (γ ≈ 0 or positive). The position γ's are reported to check this story, descriptively.
**Model v13 (position level):** For bad-weather rows, median × (1 + γ_pos). It uses exactly the prime-time machinery (`situation_multiplier`): LAD through the origin on earlier bad-weather, fantasy-relevant player-games, bootstrap se over games, EB shrinkage toward 0. Fitting uses the **fixed estimator** (seasons ≥ 2020 only).
**No player-level version:** A typical player has only a handful of bad-weather games, and player-level splits failed in both Week 1 (v11p) and prime time (v12p). The "cold-weather QB" narrative is noted but not tested.
**Placebos (two, both fixed seed):**
  1. **Random games:** the bad-weather label goes to the same number of random games each week. This checks the procedure itself, as with prime time.
  2. **Random outdoor games:** the label goes to the same number of random *outdoor/open* games each week. This separates weather from simply being outdoors. If v13 only beats placebo 1, the gain is an outdoor effect, not weather.
**Test:** Re-tuned per fold as in every experiment.
  - Pool: the Big-60 union, **restricted to bad-weather player-games**, paired bootstrap clustered by season-week.
  - **Headline pool: OOS 2021–23.** With the fixed estimator, 2020 has no earlier calibrated season to learn from, so v13 = v8m there by construction. We decide this now, before results, instead of diluting the test as the Week 1 re-run had to (that re-run had to keep its original pool).
  - **Adopt v13 only if p < 0.05 on the headline AND v13 beats both placebos** on each placebo's own labelled rows.
  - Secondary: all players on bad-weather rows; full-season Big-60.
**Diagnostics (descriptive):** v8m's share above the median and median error in bad weather vs other outdoor games vs domes, by position and by cause (wind only / cold only / both). Floor/ceiling coverage in bad weather.
**Power:** About 14% of outdoor games, roughly 9% of all games, so expect a few hundred Big-60 rows in 2021–23. Only a sizeable effect (around 0.15+ points) is detectable.
**Expectation:** Most likely a null for the same reason as prime time: the betting total already prices weather. The 2022–23 gaps also blur the label.

### 2026-11-02: Weather effect: result; REJECTED
**Headline (pre-registered): v13 vs v8m, Big-60 bad-weather player-games, OOS 2021–23 (n = 345):** +0.039 [−0.035, +0.118], p = 0.84. It is worse. **Rejected.** Secondary checks agree: all players on bad-weather rows −0.004 (p = 0.33); full-season Big-60 +0.004.
**Placebos:**
  - Random games: +0.070 (also worse). Unlike prime time, the placebo γ's are mostly ≈ 0, so the fixed estimator is behaving.
  - Random outdoor games: shrunk to exactly zero in every fold (B = 1). There is no "outdoor" residual for the weather flag to borrow.
**What the fit learned:** In 2022–23 the raw bad-weather γ's are negative for every position (WR −13 to −15%, QB −4 to −11%, RB −7 to −8%). After shrinkage (B ≈ 0.35–0.7), WR is about −9%. Out of sample, that cut hurt QBs and WRs more than it helped.
  - The reallocation story (RBs hold up while passers suffer) is **not** supported: RBs also come in negative.
  - In the 2021 fold, with one season to learn from, everything was shrunk to 0.
**Diagnostic (descriptive):** In bad weather, 45.1% of top players beat their median, vs 48.9% in fine outdoor games. The gap is small (4 points on 494 rows), and the walk-forward estimator could not turn it into lower error. Floor/ceiling coverage is 81.8%, fine.
**Limits that weaken the test, all disclosed in advance:**
  - There is no precipitation field.
  - 132 outdoor games in 2022–23 are missing weather and count as normal.
  - The values are observed at kickoff, not forecasts.
  - A better data source could change the answer. That is a reason to re-test weather only once the live pipeline has forecast data, under a new pre-registration, never on 2024/2025.
**Logged as a failed feature** (rigor rule 3).
**Unplanned observation (NOT tested, NOT a finding):** In dome/closed-roof games, 55.1% of top players beat their median (median error −0.89), vs 48.9% in fine outdoor games. This was noticed in the diagnostics, *after* looking at the data, so it is a hypothesis only. If it is tested, it needs its own pre-registration, placebo and the same adoption rule, and the write-up must say how the idea arose (forking-paths risk).

### 2026-11-02: Opponent strength by position (v14): pre-registration (written before results)
**Idea:** "Defense vs position". Some defenses give up more to a position (e.g. a weak linebacker group leaks points to TEs) than their overall quality suggests. CLAUDE.md lists it as "opponent strength (vs. position, adjusted for schedule)".
**Economic story, and why it might already be priced:**
  - Our median already uses the betting total and spread, which price the opponent's **overall** defensive quality.
  - What the team total does *not* price is **which position** the defense is weak against. Bettors price that in player props, which we don't use.
  - So the only effect left to find is position-specific. Popular "points allowed vs position" tables are thought to be mostly noise because they ignore who the defense faced. Rigor rule 2 (shrinkage) is the right tool for exactly this.
**Schedule adjustment, built in:** We measure a defense by how much players **beat or missed their own pre-game median** against it, not by raw points allowed. A defense that faced elite WRs isn't punished for allowing points the WRs were expected to score anyway, because the median already includes who the players were.
**Definition (fixed in advance):**
  - Opponent = the other team in the game.
  - For defense d, position p, game k: g_k = Σ actual / Σ v8m median over fantasy-relevant players of position p facing d, minus 1. The weight is w_k = Σ median, i.e. the expected points in that matchup.
  - Raw effect before a game = decay-weighted average of d's earlier g_k at that position. Decay has a **half-life of 8 defense-games**, fixed in advance (same as the baseline) and not tuned. It carries across seasons, so early-season weeks lean on last year's defense, faded.
  - Only games from seasons ≥ 2020 are used: the first calibrated median, the fixed estimator.
  - **No look-ahead:** the effect for week W uses only games before week W. Residuals are known once those games finish, and the median is itself a pre-game number.
**Shrinkage (empirical Bayes, per position):** Noise per game is σ²_p / w_k, so the raw effect's sampling variance is σ²_p · Σλ²w / (Σλw)², with λ the decay weights.
  - σ²_p and the true spread across defenses τ²_p are estimated by method of moments from seasons 2020..s−1 only (walk-forward).
  - B = sampling variance / (sampling variance + τ²_p); shrunk effect δ = (1 − B) · raw.
  - **Model v14: median × (1 + δ_{opponent, position}).** The per-season B's and τ² are reported.
**Placebo:** Each team's opponent is replaced by a random *other* team from the same week, with a fixed seed, before anything is fitted. A genuine defense effect should vanish. If the placebo also "helps", the gain is a generic recalibration.
**Test:** Re-tuned per fold as in every experiment. Pool: the Big-60 union, **all weeks** (v14 adjusts every row). Paired bootstrap clustered by season-week.
  - **Headline: v14 vs v8m, OOS 2021–23.** 2020 has no earlier season to estimate τ² from, so v14 = v8m there by construction (the same reasoning as weather, decided in advance).
  - **Adopt only if p < 0.05 AND v14 has lower MAE than v14-placebo** (paired, reported with its p).
  - Secondary: all players; per-position MAE; the descriptive 2020–23 pool.
**Diagnostics:**
  - τ²_p by position: how much real spread between defenses exists.
  - The distribution of shrunk effects.
  - A "stickiness" check: whether a defense's effect in the first half of a season predicts the second half, per position.
**Power:** About 3,700 Big-60 rows in 2021–23, so a 0.03-point improvement is detectable. **Expectation:** Small. TE and WR are the most plausible positions; most effects should shrink heavily.
**Clarification, added before any results (same day):** The raw effect is measured **relative to the league-wide ratio** at that position, R_p = Σ actual / Σ median over the training seasons: raw = (decayed ΣA / decayed ΣM) / R_p − 1. Points are right-skewed, so actual points average above the *median*. Without this centering, every defense would look "weak" and v14 would shift all medians up, undoing the median calibration. τ²_p is estimated from defense-season deviations from that season's league ratio.

### 2026-11-02: Opponent strength by position: result; REJECTED
**Headline (pre-registered): v14 vs v8m, Big-60, all weeks, OOS 2021–23 (n = 3,853):** −0.000 [−0.021, +0.020], p = 0.49. **No improvement; rejected.** v14 vs placebo −0.001 (p = 0.46). All players −0.001 (p = 0.36).
**By position (descriptive):** RB −0.015, WR −0.010 and QB −0.001, all non-significant. **TE +0.047 (worse)**, so the position where the model trusted defense effects most is where it lost.
**What the shrinkage did:**
  - QB: τ² ≈ 0, so it is fully shrunk (B 0.96). The betting total already captures the opponent for QBs.
  - RB/WR: an estimated true spread of 5–10% between defenses; B ≈ 0.7; typical δ within ±5%.
  - TE: the estimated true spread is about 20%, so B is only 0.43 and δ reached ±14% (10th/90th percentile), up to 49%.
  - The placebo's τ² is ≈ 0 at every position, so real defenses *do* differ more than shuffled ones *within a season*.
**Why it still fails: the differences don't persist.**
  - A defense's first-half deviation barely predicts its second half: correlation +0.04 to +0.07 (placebo −0.06 to +0.05).
  - The season-level spread τ² mixes a persistent part (tiny) with things like one big game or a mid-season injury, which the normal noise model doesn't separate. So EB over-trusted the TE effects.
  - Lesson for the paper: **τ² estimated at one time scale (a season) can overstate how much an effect persists at the scale you forecast at (next week).** A stickiness check belongs next to every EB fit.
**Economic reading:** After the betting total and spread, "defense vs position" carries essentially no forecastable information. This matches the view that DvP tables are mostly noise.
**Logged as a failed feature** (rigor rule 3). It is not re-tuned (e.g. a different half-life or a TE-only version): that would be searching for forks after seeing a null.

### 2026-11-03: Phase 3 decisions (Parv)
- **Non-commercial, confirmed:** the site has no ads, payments or sponsors. This is a condition of Open-Meteo's and Sleeper's free terms. If it ever changes, both need paid licences.
- **Accounts:** Parv creates the GitHub and Supabase accounts himself. Claude walks him through it and never handles passwords. Keys go only in `.env` (git-ignored) and GitHub Secrets.
- **Sleeper:** draft a permission email now (Parv sends it). Build everything else (nflverse, The Odds API, weather) without waiting for the reply. No Sleeper projections are collected or published until permission arrives.
- **The Odds API:** verify its free-tier numbers **directly** (its own pricing/docs pages, or the response headers of a real call) before relying on them. Search-result summaries are not enough.
- **Order:** run the one-time 2025 test **now**, before any live data goes public, then pull 2026 data.

### 2026-11-03: 2025 final test: pre-registration (written before running; one time only)
**What is tested:** The exact model that will go live. That is `predict()` with `reports/opp_eff_params.json` (tuned on 2019–23, validated once on 2024, then frozen), the ewma_hl8 baseline, and the walk-forward median (v8m) and floor/ceiling (v10) maps.
  - **Nothing is re-tuned.** The walk-forward pieces fit on all earlier seasons (2019–24 for 2025) automatically, by design. That is not tuning on the test season.
  - **No feature changes after this, whatever the result.** Every rejected feature stays rejected.
  - Re-tuning settings on 2019–25 for the live 2026 model would be a *new, untested* model. It is not done. The live model is the tested model.
**What has been seen of 2025 so far:** Schedule metadata only (game counts, roof/weather coverage in the weather experiment). No 2025 outcomes or errors have been looked at.
**Headline (decided now):** The **median** (our published point projection) vs the baseline on the Big-60 union of both pools. MAE, paired bootstrap clustered by week, one-sided. **"Pass" = median beats the baseline with p < 0.05.**
**Secondary, all reported whatever they show:**
  - the mean (v5) vs the baseline (the 2024 validation's headline);
  - all players;
  - per position (descriptive);
  - RMSE, Spearman, bias;
  - floor–ceiling coverage (target ~80%; not a pass/fail) and coverage by position;
  - the weekly head-to-head record on the baseline's own Big-60 (the CLAUDE.md format) and on ours.
**Comparison with the past (descriptive):** the 2025 gain is set beside OOS 2020–23 (−0.245 for v8m vs baseline) and 2024.
**One-time guard:** `scripts/test_2025.py` refuses to run if `reports/test_2025.md` exists.
**If it fails:** It gets published as a failure, in the paper and the README. The model is not tweaked to pass. Any later model is a new model, and must be judged on live 2026+ seasons.

### 2026-11-03: 2025 final test: result (PASSED). The model is final
**Headline (pre-registered): median vs baseline, Big-60 union, 2025 (n = 1,224):** 6.295 vs 6.589, diff **−0.294** [−0.410, −0.185], p < 0.001. **Pass.**
**Secondary:**
  - Mean (v5) vs baseline −0.189 (p < 0.001), so the median step adds a further −0.105 on top of the mean, as it did on dev.
  - All players −0.146.
  - RMSE 8.20 vs 8.34; Spearman 0.372 vs 0.348.
  - By position (descriptive): TE −0.36, RB −0.32, WR −0.32, QB −0.12. All four improve.
  - Head-to-head on the baseline's own Big-60: **16–2**. On our own Big-60: 15–3.
**Floor/ceiling:**
  - Big-60 coverage 82.7% (8.3% below the floor, 9.1% above the ceiling); all players 80.1%. Both are close to the 80% target.
  - QB is the weakest at 75.9%, with 15.3% below the floor. That is descriptive, and a candidate to watch in 2026; not fixed with 2025 data.
**Compared with earlier seasons (descriptive):** The v8m median gained −0.245 OOS on 2020–23 and **−0.294 on 2025**, so there is no winner's-curse shrinkage this time. The mean (v5) gained −0.188 on dev, −0.158 on 2024 and −0.189 on 2025.
**The 2024 hypotheses, checked descriptively:**
  1. The late-season weakness did not recur: the losses were weeks 5 and 7, and weeks 13–18 went 6–0. That supports reading 2024's pattern as noise, consistent with the rejected week-of-season test.
  2. The bias is not under-projection this time: the mean is +0.49 and the median −0.42, which is expected for a median of a right-skewed outcome.
**2025 is now spent.** `scripts/test_2025.py` refuses to re-run. The model in `reports/opp_eff_params.json` with `predict()` is the **final, tested live model**. Any future change is a new model, judged only on live 2026+ seasons under a new pre-registration.

### 2026-11-03: Live data storage, first 2026 pull, and the status of The Odds API
- **Live pulls are kept separate and timestamped:** `data/live/<season>/<UTC stamp>/`. The frozen `data/raw/` (2018–25) is never re-downloaded or overwritten, so every committed result still reproduces. nflverse revises old data from time to time, and re-pulling would silently change past numbers.
  - Every pull is kept (it is small), so for any frozen projection we can later show exactly which data it was made from.
- **First pull (2026-11-03 21:35 UTC):** weeks 1–8 played (121 games); stats, snaps and injuries for weeks 1–8. **All 15 week-9 games have a spread and total in nflverse.** No temperature/wind for upcoming games.
- **The Odds API: not verified, so not relied on.** Its website refused every automated connection from here. Parv will check the free-plan figures in a browser, and if we sign up, the first call's quota headers settle it. Because nflverse already carries next-week lines, The Odds API is now a *backup* for line freshness and timestamps, not a requirement.

### 2026-11-03: Live rows for upcoming games: who gets a projection (rule fixed before building)
**Candidates for team T's game in week W of season S:** every skill player whose **most recent game** in our data was for T (so traded players move with their new team), and who played for T at least once **in season S before week W**. In Week 1, when there are no season-S games yet, his most recent game (last season) must have been for T.
  - **Excluded up front:** players designated **Out** for week W in the injury report, once that report exists (Wednesday–Friday). They are logged separately, and the same rule will apply to every source in the Big 60 (CLAUDE.md inactive policy). Doubtful/Questionable players keep their projection and are flagged.
  - **Teams on bye** get no rows.
**Known limits (disclosed):**
  - Players with **no NFL game history** (rookies who haven't played, new signings with no snaps yet) get no projection. The baseline and the model both need at least one earlier game, so this is the same for both.
  - Players returning from a long absence are projected from their older history, faded by the usual decay.
  - Late scratches after the last injury report are handled by the inactive policy at kickoff.
**Data:** History is the frozen 2018–25 files plus the latest live 2026 pull. The player-ID crosswalk is the frozen table, with only *new* IDs added from the live pull, so 2018–25 history is built exactly as before.
**Proof of no look-ahead (required before use):** On past weeks, rebuilding a week as "upcoming" from only earlier data (results blanked, later weeks deleted) must reproduce the full-data median, floor and ceiling for the same players **exactly**.

### 2026-11-03: Live rows: result of the no-look-ahead proof, and a roster gap
**Proof (`scripts/check_live.py`, 2021 wk 14, 2023 wk 1, 2023 wk 10):** Every row rebuilt as "upcoming" from earlier data only, with the player on the same team, reproduces the full-data median, floor and ceiling **exactly** (max difference 0.0; 906 rows). **No look-ahead.**
**The gap found: roster changes.** Game history can't see trades or signings until the player's first game for his new team.
  - 2021 wk 14: Phillip Dorsett was put on SEA (his last game) instead of HOU, in the very game where he faced SEA.
  - 2023 wk 1: two TEs who moved GB → CHI; also **6 Big-60 players missed** (Hopkins, Waller, J. Williams, Ridley, Montgomery, Swift), all offseason moves.
  - Mid-season the effect is small: 0–1 wrong-team rows per week, and no Big-60 player missed in weeks 10/14. **In Week 1 it is serious.**
**Fix proposed (needs Parv's OK, because it is a new download):** Take each player's *current team* from nflverse rosters (`load_rosters_weekly`), which reflect transactions before the game, instead of from his last game. A new no-look-ahead check must then confirm that the roster used for week W is one published before week W's kickoff.
**First live run (2026 week 9, local only, nothing published):** 529 players projected, all with a median, floor and ceiling. Nobody is excluded yet, because the week-9 injury report comes out Wednesday–Friday. Projections are saved next to the data pull they came from.

### 2026-11-03: Roster data for live rows (Parv approved the download; rule fixed before building)
**Source:** nflverse weekly rosters (`load_rosters_weekly`), one snapshot per team-week, plus for the live season the current season roster (`load_rosters`), saved inside the timestamped live pull. The frozen 2018–25 rosters are a **new** file, `data/raw/rosters_weekly.parquet`; no existing file changes.
**Rule: a player's team for week W:**
  - **Past seasons (checks and backtests):** his team on the **week-W roster**. Only the *team* field is used, which is public before kickoff (trades and signings are announced). The game-day status (e.g. INA = inactive, announced about 90 minutes before kickoff) is **not** used, because the live pipeline can't rely on getting it in time.
  - **Live season:** the week-W roster isn't published until about game day (on Tuesday of week 9, the latest is week 8). So we use the **current season roster from our own timestamped pull**, which is pre-game by construction.
  - If a player is missing from the roster, he falls back to his last game's team.
**Who is a candidate:**
  - **Included:** players on T's roster with a skill position, at least one earlier NFL game (the model needs history), and a game this season (any team) or, in Week 1, last season.
  - **Excluded on pre-game status:** reserve lists (RES, e.g. injured reserve), practice squad (DEV), cut, retired. Each is a public transaction made before the game. Players designated **Out** are excluded as before.
**Check:** re-run `check_live.py`. Same-team rows must still match exactly, wrong-team rows should fall to about 0, and Week 1 should no longer miss the offseason movers.

### 2026-11-03: Rosters added: result
**Re-check (`check_live.py`):**
  - **Wrong-team rows: 0** (was 1 and 2).
  - **Big-60 players missed in Week 1: 1** (was 6). The one left is Calvin Ridley, who didn't play in 2022 (suspension), so the "played last season" rule leaves him out. That is a disclosed limit, the same for the baseline.
  - Same-team rows still match **exactly**: no look-ahead.
  - Fewer candidates who then didn't play (e.g. 2021 wk 14: 203 → 80), because reserve and practice-squad players are now excluded before the game.
**Live 2026 week 9 (new pull 2026-11-04 04:20 UTC):** 448 players projected (was 529 without rosters; the difference is reserve, practice-squad and cut players). The team comes from the current roster saved in that pull, since the week-9 weekly roster isn't published yet. The old 2026 pull folder (without rosters) is kept for the record but is no longer "complete", so it is never used.
