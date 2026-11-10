-- Adds leaderboard_highlights (same definition as db/schema.sql), readable by the public site. Names only.
CREATE TABLE IF NOT EXISTS leaderboard_highlights (
    -- Biggest wins/losses vs each platform per week: NAMES ONLY, no errors or projections (DECISIONS.md 2026-11-10).
    platform        TEXT NOT NULL,
    season          INTEGER NOT NULL,
    week            INTEGER NOT NULL,
    kind            TEXT NOT NULL CHECK (kind IN ('win', 'loss')),
    rank            INTEGER NOT NULL,
    player_id       TEXT NOT NULL,
    player_name     TEXT NOT NULL,
    position        TEXT NOT NULL,
    PRIMARY KEY (platform, season, week, kind, rank)
);
ALTER TABLE leaderboard_highlights ENABLE ROW LEVEL SECURITY;
CREATE POLICY public_read ON leaderboard_highlights FOR SELECT TO anon USING (true);
