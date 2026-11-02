# CLAUDE.md — Fantasy Projection Engine

Read this file at the start of every session. It is the project's source of truth.

## Who you're working with
- **Parv** — Head Economist & Project Manager. High school student, strong in economics/statistics, **zero coding experience**.
- **You (Claude Code)** — Lead Software Engineer. You write, run, test, and maintain all code.
- Explain every step in plain English: what you did, why, and what Parv should check. Ask before anything destructive or that costs money.
- Parv must be able to *defend every modeling choice* in an interview. Favor interpretable methods over black boxes, and explain the economics/statistics behind each one.

## What we're building
A redraft fantasy football (full PPR) weekly projection engine that beats a simple average by modeling **multi-year situational effects**, and publicly grades itself every week.

**Core differentiator:** situational adjustments (Week 1 efficiency, late-season workload ramps, prime-time splits, target-share stability), estimated statistically and shrunk toward league averages — never hand-coded hunches.

## Non-negotiable rigor rules
1. **No look-ahead leakage.** Any projection for week W may only use data available before week W kicked off. All backtests are walk-forward.
2. **Shrinkage for small samples.** Player-specific situational effects (e.g., a player's 4 career Week 1 games) use empirical Bayes / partial pooling toward position-level effects. Report how much each effect was shrunk.
3. **Earn every feature.** A feature only enters the model if it reduces out-of-sample error on held-out seasons. Log failed features too — they go in the paper.
4. **Holdout discipline.** Develop on 2018–2023, validate on 2024, final test on 2025 once. Do not tune on the test season.
5. **Fair comparison.** Same scoring (full PPR), same player pool, projections frozen before kickoff for every source.
6. **Significance, not just "wins."** Compare our errors vs. consensus with a paired test (e.g., Diebold–Mariano or paired bootstrap on per-player absolute errors), not only "lower MAE this week."

## "The Big 60" leaderboard
- **Format: head-to-head per platform.** For each platform (e.g., ESPN, Yahoo, Sleeper), the pool is *that platform's own* pre-game top 10 QB, 20 RB, 20 WR, 10 TE by its projected points, frozen at kickoff. Compare that platform's projections vs. ours on exactly those 60 players after games finish. Lower MAE wins the week.
- Never select the pool by actual points afterwards — selecting on outcomes biases the test.
- Output per platform: weekly MAE (ours vs. theirs), weekly winner, running season record (e.g., "9–3 vs ESPN"), and per-position breakdown.
- Metric: MAE on fantasy points (primary). Also report RMSE and rank correlation (Spearman) as secondary.
- Inactive/ruled-out players: document a single policy (default: excluded if inactive at kickoff, logged separately) and apply it identically to every source.
- Publish weekly results plus a running season total, including weeks we lose.

## Model design (build in this order)
1. **Baseline:** trailing weighted average of PPR points. This is the bar everything must beat.
2. **Opportunity × Efficiency:** project opportunity (snap %, target share, carry share, red-zone share, air-yards share) separately from efficiency (points per opportunity).
3. **Situational modifiers (shrunk):** week-of-season ramp, Week 1 effect, prime-time slot, dome/outdoor & cold weather, opponent strength (vs. position, adjusted for schedule).
4. **Uncertainty:** 10th/50th/90th percentile (floor/median/ceiling). Check calibration — ~80% of outcomes should land between floor and ceiling.
5. **Explainability:** store each adjustment per player-week so the site can show "Baseline 17.2 → −1.8 Week 1 effect → 15.4."

Deferred (data is paywalled, manual, or too thin): coverage-scheme matchups, contract-year effects, holdout flags.

## Data sources
- **nflreadpy** (nflverse): weekly player stats, play-by-play, snap counts, schedules (game time → prime-time flag, roof, temp), injuries, depth charts.
- **Consensus benchmark:** to be decided and verified. Historical ESPN/Yahoo projections are NOT freely available, so backtests compare against our baseline and any archived source we can verify. Live season: snapshot consensus projections automatically before kickoff every week and store them with a timestamp. Respect each site's terms of service; prefer official or documented APIs.
- **Injuries:** use structured nflreadpy injury/practice data as model inputs. An LLM may help classify free-text news later, but it never invents projection numbers.

## Stack
- Python (managed with `uv` and a project virtual environment — never install into system Python), polars/pandas, scikit-learn, statsmodels.
- Supabase (Postgres) for projections, actuals, consensus snapshots, and leaderboard results.
- Next.js + Tailwind (+ shadcn/ui) on Vercel. Single public dashboard, no user logins for v1.
- GitHub repo; GitHub Actions runs the scheduled pipeline (daily + extra in-season runs). Secrets stored in GitHub Secrets / `.env` (never committed).

## Automated pipeline (in-season) — live projections, frozen grading
Projections are **living**: they refresh automatically as inputs change. Grading is **frozen**: only the snapshot taken at each game's kickoff counts for the Big 60.

**Daily (early morning PT):** pull latest stats, injuries/practice reports, depth charts, transactions, betting lines, weather forecasts → re-run model → publish to Supabase/site. Log what changed and why per player.
**Thu–Sun, every ~3 hours:** extra refresh runs (injury news moves fastest).
**At each game's kickoff:** freeze projections for that game with a timestamp; snapshot consensus at the same time.
**Tue:** ingest actuals → score frozen projections → update Big 60 leaderboard and running totals.
**On failure:** open a GitHub issue / send an alert with the error and its plain-English cause. A failed run must never overwrite the last good projections.

Known limit: news breaking minutes before kickoff may be missed if no free source has it yet; handle via the inactive-player policy and log these cases.

## Dynamic inputs the model must react to
- **Injuries & practice status** (DNP/Limited/Full, game designation) → adjust expected snaps/opportunity, using effects estimated from history.
- **Teammate availability (vacated opportunity):** when a player is out or limited, redistribute his expected targets/carries to teammates using historically estimated reallocation shares (by position/role), not a flat split. Same logic for QB changes (backup QB lowers efficiency for pass catchers).
- **Depth chart & transactions:** trades, releases, practice-squad elevations update roles.
- **Recent performance:** each week updates baselines, opportunity shares, and trend estimates (with shrinkage so one game doesn't overreact).
- **Betting market:** game total and spread → implied team points, a strong prior for team scoring and game script. Verify a free/low-cost odds source and its terms before relying on it.
- **Weather forecast:** wind, precipitation, temperature for outdoor games, refreshed as kickoff nears.
Every input still has to earn its place on held-out seasons (rigor rule 3).

## Roadmap
- **Phase 1 — Foundation:** environment, repo, data pull 2018–2025, data-quality checks, naive baseline + MAE.
- **Phase 2 — Model:** opportunity × efficiency, shrunk situational effects, injury + vacated-opportunity reallocation, betting-market prior, walk-forward backtest, feature log.
- **Phase 3 — Benchmark & storage:** consensus snapshot pipeline, Supabase schema, Big 60 scoring.
- **Phase 4 — Automation:** GitHub Actions schedule, alerts, tests.
- **Phase 5 — Website:** projections table (floor/median/ceiling), player breakdown, Big 60 accountability page, methodology page.
- **Phase 6 — Paper:** methodology, results incl. failures, limitations. Live leaderboard runs the rest of 2026 and fully in 2027.

## Working conventions
- Small, reviewable steps. After each step: summary, how to verify, what's next.
- Every module has tests for its math (MAE, shrinkage, leakage checks).
- Keep a `DECISIONS.md` log: date, decision, reason (Parv's economic reasoning goes here).
- Plain-English README for non-coders.
