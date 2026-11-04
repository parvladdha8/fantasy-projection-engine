"""Tests for plain-English failure causes."""

from fantasy_projection_engine.alerts import plain_cause


class OperationalError(Exception):
    pass


def test_known_causes_are_explained():
    assert "paused" in plain_cause(OperationalError("connection failed"))
    assert "secret" in plain_cause(RuntimeError("SUPABASE_DB_URL is not set (in .env locally, or as a GitHub Secret)."))
    assert "fingerprint" in plain_cause(RuntimeError("checksum mismatch for schedules.parquet"))
    assert "refused to publish" in plain_cause(RuntimeError("only 3 players projected for week 9; refusing to publish"))
    assert "download failed" in plain_cause(OSError("HTTP Error 503"))


def test_unknown_error_still_gets_a_sentence():
    assert plain_cause(KeyError("median")).startswith("An unexpected error")


def test_failure_report_hides_database_secrets(tmp_path, monkeypatch):
    from fantasy_projection_engine.alerts import write_failure
    url = "postgresql://postgres.myref:s3cr@t@aws-0-us-east-1.pooler.supabase.com:5432/postgres"
    monkeypatch.setenv("SUPABASE_DB_URL", url)
    text = write_failure("test", RuntimeError(f"failed for user postgres.myref with s3cr@t via {url}"), tmp_path / "f.md")
    assert "s3cr@t" not in text and "postgres.myref" not in text and "pooler.supabase.com:5432" not in text
