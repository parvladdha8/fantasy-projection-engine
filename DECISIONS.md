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
