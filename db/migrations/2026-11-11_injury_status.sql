-- Adds each projection's latest injury status and historical chance of playing (DECISIONS.md 2026-11-11).
ALTER TABLE projections ADD COLUMN IF NOT EXISTS injury_status TEXT;
ALTER TABLE projections ADD COLUMN IF NOT EXISTS p_play DOUBLE PRECISION;
