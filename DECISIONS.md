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
