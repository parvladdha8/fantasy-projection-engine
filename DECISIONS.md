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
**Decision (for now):** Accept that nflverse weekly stats only include a player-week if he recorded a stat. An active WR with 0 targets is mostly missing rather than listed at 0 points.
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
