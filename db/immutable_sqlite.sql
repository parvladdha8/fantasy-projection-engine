-- SQLite version of "frozen means frozen" (local tests). Postgres version: db/immutable_postgres.sql.
CREATE TRIGGER IF NOT EXISTS frozen_no_update BEFORE UPDATE ON frozen_projections
BEGIN SELECT RAISE(ABORT, 'frozen_projections is immutable'); END;
CREATE TRIGGER IF NOT EXISTS frozen_no_delete BEFORE DELETE ON frozen_projections
BEGIN SELECT RAISE(ABORT, 'frozen_projections is immutable'); END;
