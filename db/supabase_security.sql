-- Supabase security: run AFTER schema.sql and immutable_postgres.sql.
-- Supabase exposes every table through a public web API using the project's public ("anon") key, which our
-- website will use and anyone can see. Row Level Security (RLS) blocks everything by default; the policies
-- below then allow READ-ONLY access to what the site should show. Nothing allows public writes.
-- The pipeline writes through the private database connection (password in .env / GitHub Secrets), which
-- RLS does not restrict.

ALTER TABLE runs                  ENABLE ROW LEVEL SECURITY;
ALTER TABLE projections           ENABLE ROW LEVEL SECURITY;
ALTER TABLE consensus_snapshots   ENABLE ROW LEVEL SECURITY;
ALTER TABLE frozen_projections    ENABLE ROW LEVEL SECURITY;
ALTER TABLE actuals               ENABLE ROW LEVEL SECURITY;
ALTER TABLE inactive_log          ENABLE ROW LEVEL SECURITY;
ALTER TABLE leaderboard_weekly    ENABLE ROW LEVEL SECURITY;
ALTER TABLE leaderboard_position  ENABLE ROW LEVEL SECURITY;
ALTER TABLE leaderboard_highlights ENABLE ROW LEVEL SECURITY;

-- Public read: our projections, run status, actual points, inactive log, leaderboard.
CREATE POLICY public_read ON runs                 FOR SELECT TO anon USING (true);
CREATE POLICY public_read ON projections          FOR SELECT TO anon USING (true);
CREATE POLICY public_read ON actuals              FOR SELECT TO anon USING (true);
CREATE POLICY public_read ON inactive_log         FOR SELECT TO anon USING (true);
CREATE POLICY public_read ON leaderboard_weekly   FOR SELECT TO anon USING (true);
CREATE POLICY public_read ON leaderboard_position FOR SELECT TO anon USING (true);
CREATE POLICY public_read ON leaderboard_highlights FOR SELECT TO anon USING (true);

-- Frozen projections: only OUR model and our baseline are public. Platforms' frozen projections stay private
-- (their terms may only allow showing the 60 benchmark players; that table will be added with permission).
CREATE POLICY public_read_own ON frozen_projections FOR SELECT TO anon USING (source IN ('ours', 'baseline'));

-- consensus_snapshots: no policy → not readable through the public API at all.

-- Added 2026-11-05 (db/migrations/2026-11-05_weather.sql): weather forecasts, public read-only.
ALTER TABLE weather_forecasts ENABLE ROW LEVEL SECURITY;
CREATE POLICY public_read ON weather_forecasts FOR SELECT TO anon USING (true);
