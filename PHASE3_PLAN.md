# Phase 3 plan: live data, storage and Big 60 scoring (draft for Parv's approval)

Written 2026-11-03. Nothing below has been installed, signed up for or downloaded yet. Each **[decision]** needs Parv's OK.

## Where we are
- The model is frozen (v5 mean, v8m median, v10 floor/ceiling) and runs through one entry point, `predict.py`.
- Our local data stops at the 2025 season. **The 2026 season is live (around week 9)**, so the pipeline needs 2026 data first.
- There is no GitHub remote yet. The repo exists only on this laptop.

## Progress (2026-11-03)
- **Done:**
  - Decisions 1–4 answered (see DECISIONS.md).
  - The 2025 final test passed (−0.294 pts MAE, p < 0.001).
  - The Sleeper email is drafted (`outreach/sleeper_permission_email.md`); Parv sends it.
- **2026 data pulled** to `data/live/2026/<timestamp>/`. The frozen `data/raw/` was not touched.
  - Weeks 1–8 are played.
  - **Every week-9 game already has a spread and total in nflverse.** Later weeks mostly don't, as expected, since books post lines about a week ahead.
  - Upcoming games have **no** temperature/wind, so forecasts must come from Open-Meteo.
- **The Odds API is NOT yet verified.** Its site resets every automated connection (both curl and the web fetcher), so its numbers can't be read from here.
  - Direct verification plan: Parv opens the pricing page in a browser and confirms the free-plan figures. If we sign up, the first real call's response headers (`x-requests-remaining`, `x-requests-used`, `x-requests-last`) are the authoritative check.
  - Until then it is not relied on. nflverse lines cover the next week, so The Odds API is a backup for line freshness, not a blocker.

## Sources checked (cost and terms)

| Need | Source | Cost | Terms / limits (checked 2026-11-03) | Verdict |
|---|---|---|---|---|
| Stats, schedules, injuries, depth charts | **nflverse via nflreadpy** (already used) | Free | Open data. Schedules include unplayed games. **Not yet verified:** whether lines are filled in for upcoming games | Keep. Verify lines on the first 2026 pull |
| Betting lines (backup / fresher) | **The Odds API**, free "Starter" plan | Free (500 credits/month) | Cost = markets × regions per call; empty responses are free; no historical odds on the free plan. Spreads + totals, US region = **2 credits per call for every NFL game** | Use only if nflverse lines prove stale. 2 pulls/day ≈ 120 credits/month, well under 500 |
| Weather forecasts | **Open-Meteo** | Free | **Non-commercial only**; under 10,000 calls/day; data CC BY 4.0, so **attribution required** on the site; no API key | Fits. Needs a table of stadium coordinates (~30 rows, entered once and checked) |
| Database | **Supabase**, free plan | Free | 500 MB database, 5 GB egress, 2 active projects, **paused after 1 week of inactivity** (our daily runs prevent that). Pro is $25/month (not needed) | Fits. Our data is a few MB per season |
| Platform projections (Big 60) | **Sleeper** | Free | Official docs: "free to use for non-commercial purposes", stay under 1000 calls/minute. **The projections endpoint is NOT in the official docs** (only community wrappers use it) | **Gray area. See decision 3** |
| | ESPN | Free | No public, documented API; scraping its fantasy site is against its terms | Don't use |
| | Yahoo Fantasy API | Free | Official, documented API, but needs OAuth app registration and access is tied to a league | Possible second platform later |
| Inactives at kickoff | nflverse injury designations + Sleeper player status (documented endpoint, at most once a day) | Free | As above | Known limit (CLAUDE.md): late scratches may be missed; logged under the inactive policy |

## Decisions for Parv
1. **[decision] Non-commercial.** Open-Meteo and Sleeper are free *because* we are non-commercial. Confirm the site has no ads, payments or sponsorships. If that ever changes, those two sources need paid licences.
2. **[decision] Accounts.** Supabase and GitHub (and The Odds API, if needed) need accounts *in your name*. You create them; I never see your password. Keys go into `.env` (already git-ignored) and GitHub Secrets.
3. **[decision] Sleeper projections.** Options:
   - (a) Email Sleeper's developer contact and ask permission to snapshot weekly projections for a non-commercial accuracy leaderboard. Start Big 60 only after a yes. (**Recommended**, the cleanest for an interview.)
   - (b) Use the undocumented endpoint under the general non-commercial terms, and disclose it.
   - (c) Launch the leaderboard against our own baseline only, and add platforms as permission arrives.
4. **[decision] 2025 final test timing.** Live 2026 grading doesn't touch 2025, but the model should be final before we publish live numbers. Run the one-time 2025 test **before** going live (recommended), so the paper's test result and the live model are the same model.

## Build order (small, reviewable steps; each with tests)
1. **Pull 2026 data** (nflreadpy; a download, so it needs your OK). Check data quality. Verify whether upcoming games have lines.
2. **Live rows:** build player rows for the *upcoming* week (no actual points yet) so `predict()` can project games that haven't happened. Test that no row uses information from after its kickoff.
3. **Storage schema** (designed locally first, as plain SQL), with these tables:
   - `projections`: every refresh, timestamped
   - `frozen_projections`: the snapshot at kickoff, never edited
   - `consensus_snapshots`
   - `actuals`
   - `inactive_log`
   - `leaderboard`
4. **Big 60 scoring:** score the frozen projections against actuals, each platform's own top-60 pool, MAE/RMSE/Spearman, weekly winner, running record. The inactive policy is applied identically to every source. Tests come first, using made-up data.
5. **Connect Supabase** (after your accounts exist): write the tables and run one end-to-end dry run.
6. **Weather forecasts** (stored for the future re-test of weather; **not** used in projections, since weather was rejected).
7. **Consensus snapshots** (after decision 3).

Phase 4 (GitHub Actions schedule, alerts) comes after this.

## Sources
- [Supabase pricing](https://supabase.com/pricing)
- [Open-Meteo terms](https://open-meteo.com/en/terms)
- [Sleeper API docs](https://docs.sleeper.com/)
- The Odds API: [docs v4](https://the-odds-api.com/liveapi/guides/v4/), [FAQs](https://the-odds-api.com/manage/faqs.html) (the site was unreachable from here; figures come from search results of its own pages and must be re-checked before signing up)
