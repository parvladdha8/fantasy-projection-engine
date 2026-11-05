-- Adds columns needed to freeze platform snapshots by game (same as db/schema.sql). consensus_snapshots stays private.
ALTER TABLE consensus_snapshots ADD COLUMN IF NOT EXISTS team TEXT;
ALTER TABLE consensus_snapshots ADD COLUMN IF NOT EXISTS game_id TEXT;
ALTER TABLE consensus_snapshots ADD COLUMN IF NOT EXISTS projected_platform DOUBLE PRECISION;
