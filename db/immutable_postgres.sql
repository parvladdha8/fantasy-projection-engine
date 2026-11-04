-- Postgres (Supabase) version of "frozen means frozen": any UPDATE or DELETE on frozen_projections fails.
CREATE OR REPLACE FUNCTION refuse_change() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'frozen_projections is immutable';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS frozen_immutable ON frozen_projections;
CREATE TRIGGER frozen_immutable BEFORE UPDATE OR DELETE ON frozen_projections
FOR EACH ROW EXECUTE FUNCTION refuse_change();
