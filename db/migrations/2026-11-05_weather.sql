-- Adds the weather_forecasts table to an existing database (same definition as db/schema.sql), with RLS.
CREATE TABLE IF NOT EXISTS weather_forecasts (
    game_id TEXT NOT NULL, fetched_at TEXT NOT NULL, kickoff TEXT NOT NULL, stadium_id TEXT NOT NULL, roof TEXT,
    latitude DOUBLE PRECISION NOT NULL, longitude DOUBLE PRECISION NOT NULL,
    temp_f DOUBLE PRECISION, wind_mph DOUBLE PRECISION, gust_mph DOUBLE PRECISION, precip_mm DOUBLE PRECISION,
    precip_prob DOUBLE PRECISION, snow_cm DOUBLE PRECISION, source TEXT NOT NULL,
    PRIMARY KEY (game_id, fetched_at), CHECK (fetched_at < kickoff)
);
ALTER TABLE weather_forecasts ENABLE ROW LEVEL SECURITY;
CREATE POLICY public_read ON weather_forecasts FOR SELECT TO anon USING (true);
