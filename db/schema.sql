-- Fantasy Projection Engine: storage schema.
-- Plain SQL that runs on Postgres (Supabase) and on SQLite (local tests). Timestamps are UTC ISO-8601 text
-- ("2026-11-08T18:00:00Z"), which sorts correctly as text on both. Rules: DECISIONS.md, 2026-11-04.

-- One row per pipeline run. The site shows projections from the latest run with status = 'ok'.
CREATE TABLE IF NOT EXISTS runs (
    run_id          TEXT PRIMARY KEY,
    started_at      TEXT NOT NULL,
    finished_at     TEXT,
    status          TEXT NOT NULL CHECK (status IN ('running', 'ok', 'failed')),
    data_pull       TEXT,            -- data/live/<season>/<stamp> the run was built from
    code_version    TEXT,            -- git commit
    error           TEXT             -- plain-English cause when status = 'failed'
);

-- Every refresh of every projection (living projections). Never updated in place.
CREATE TABLE IF NOT EXISTS projections (
    run_id          TEXT NOT NULL REFERENCES runs(run_id),
    player_id       TEXT NOT NULL,
    game_id         TEXT NOT NULL,
    season          INTEGER NOT NULL,
    week            INTEGER NOT NULL,
    player_name     TEXT,
    position        TEXT NOT NULL CHECK (position IN ('QB', 'RB', 'WR', 'TE')),
    team            TEXT NOT NULL,
    median          DOUBLE PRECISION,
    floor           DOUBLE PRECISION,
    ceiling         DOUBLE PRECISION,
    baseline        DOUBLE PRECISION,  -- trailing-average projection (the 'baseline' platform), same run
    explanation     TEXT,
    PRIMARY KEY (run_id, player_id, game_id)
);

-- Platform projections as captured (raw snapshots, every capture kept).
CREATE TABLE IF NOT EXISTS consensus_snapshots (
    source            TEXT NOT NULL,   -- e.g. 'sleeper'
    source_player_id  TEXT NOT NULL,
    player_id         TEXT,            -- our (nflverse gsis) id, if matched
    season            INTEGER NOT NULL,
    week              INTEGER NOT NULL,
    position          TEXT,
    projected         DOUBLE PRECISION,
    captured_at       TEXT NOT NULL,
    PRIMARY KEY (source, source_player_id, season, week, captured_at)
);

-- The snapshot that counts: one per source, player and game, taken at or before kickoff. Immutable.
CREATE TABLE IF NOT EXISTS frozen_projections (
    source          TEXT NOT NULL,     -- 'ours', 'baseline', 'sleeper', ...
    player_id       TEXT NOT NULL,
    game_id         TEXT NOT NULL,
    season          INTEGER NOT NULL,
    week            INTEGER NOT NULL,
    position        TEXT NOT NULL CHECK (position IN ('QB', 'RB', 'WR', 'TE')),
    team            TEXT,
    projected       DOUBLE PRECISION NOT NULL,
    floor           DOUBLE PRECISION,
    ceiling         DOUBLE PRECISION,
    kickoff         TEXT NOT NULL,
    frozen_at       TEXT NOT NULL,
    origin          TEXT,              -- run_id (ours/baseline) or captured_at (platforms)
    recorded_at     TEXT,              -- when the row was actually written (may be after kickoff if the scheduler ran late;
                                       -- frozen_at is the moment it represents, always <= kickoff)
    PRIMARY KEY (source, player_id, game_id),
    CHECK (frozen_at <= kickoff)
);

-- Actual PPR points after the games (re-ingested if the NFL issues a stat correction).
CREATE TABLE IF NOT EXISTS actuals (
    player_id       TEXT NOT NULL,
    game_id         TEXT NOT NULL,
    season          INTEGER NOT NULL,
    week            INTEGER NOT NULL,
    points_ppr      DOUBLE PRECISION NOT NULL,
    ingested_at     TEXT NOT NULL,
    PRIMARY KEY (player_id, game_id)
);

-- Players excluded under the inactive policy (same list applies to every source).
CREATE TABLE IF NOT EXISTS inactive_log (
    player_id       TEXT NOT NULL,
    game_id         TEXT NOT NULL,
    season          INTEGER NOT NULL,
    week            INTEGER NOT NULL,
    reason          TEXT NOT NULL CHECK (reason IN ('designated_out', 'inactive_at_kickoff')),
    logged_at       TEXT NOT NULL,
    PRIMARY KEY (player_id, game_id)
);

-- Big 60 results: one row per platform and week, plus the per-position breakdown.
CREATE TABLE IF NOT EXISTS leaderboard_weekly (
    platform           TEXT NOT NULL,
    season             INTEGER NOT NULL,
    week               INTEGER NOT NULL,
    n_pool             INTEGER NOT NULL,
    n_scored           INTEGER NOT NULL,
    n_dropped_no_ours  INTEGER NOT NULL,   -- pool players we had no projection for (published)
    n_inactive         INTEGER NOT NULL,   -- removed before selecting the pool (published)
    mae_ours           DOUBLE PRECISION NOT NULL,
    mae_platform       DOUBLE PRECISION NOT NULL,
    rmse_ours          DOUBLE PRECISION NOT NULL,
    rmse_platform      DOUBLE PRECISION NOT NULL,
    spearman_ours      DOUBLE PRECISION,
    spearman_platform  DOUBLE PRECISION,
    winner             TEXT NOT NULL CHECK (winner IN ('ours', 'platform', 'tie')),
    computed_at        TEXT NOT NULL,
    PRIMARY KEY (platform, season, week)
);

CREATE TABLE IF NOT EXISTS leaderboard_position (
    platform        TEXT NOT NULL,
    season          INTEGER NOT NULL,
    week            INTEGER NOT NULL,
    position        TEXT NOT NULL,
    n               INTEGER NOT NULL,
    mae_ours        DOUBLE PRECISION NOT NULL,
    mae_platform    DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (platform, season, week, position)
);
