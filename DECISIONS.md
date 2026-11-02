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
