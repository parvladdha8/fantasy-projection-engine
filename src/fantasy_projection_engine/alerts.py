"""Plain-English causes for pipeline failures (used in the GitHub issue a failed run opens)."""


def plain_cause(exc: BaseException) -> str:
    """A short, non-technical explanation of the likely cause, matched on the error's type and message."""
    name, msg = type(exc).__name__, str(exc).lower()
    if "supabase_db_url is not set" in msg:
        return "The database address is missing. Locally it lives in .env; on GitHub it is the SUPABASE_DB_URL secret."
    if name == "OperationalError" or "password authentication" in msg or "could not connect" in msg or "timeout" in msg and "connect" in msg:
        return ("Couldn't reach the Supabase database. Common causes: the free project was paused after a week of no "
                "activity (un-pause it in the Supabase dashboard), the password was changed without updating the secret, "
                "or Supabase is having an outage.")
    if "checksum" in msg:
        return ("The frozen 2018–25 data downloaded for this run doesn't match its recorded fingerprint, so the run stopped "
                "rather than project from different data. The release file may have been replaced or corrupted.")
    if "refusing to publish" in msg:
        return ("Far fewer players than usual were projected, so the run refused to publish. Usually a partial or delayed "
                "nflverse data update; the next run normally fixes itself.")
    if name in ("HTTPError", "URLError", "ConnectionError", "RemoteDisconnected", "SSLError") or "http" in msg or "download" in msg:
        return "A data download failed (nflverse's servers or the network). Usually temporary; the next scheduled run retries."
    if "no upcoming regular-season games" in msg:
        return "There are no upcoming regular-season games left this season, so there is nothing to project."
    return "An unexpected error in our code or the data. It needs a look; the error message below says where it happened."


def write_failure(step: str, exc: BaseException, path=None) -> str:
    """Write the issue text for a failed run to failure.md (git-ignored); the workflow posts it as a GitHub issue."""
    import os
    import traceback
    from pathlib import Path
    from .data import PROJECT_ROOT
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))[-3000:]
    run = os.environ.get("GITHUB_SERVER_URL", "") + "/" + os.environ.get("GITHUB_REPOSITORY", "") + "/actions/runs/" + \
        os.environ.get("GITHUB_RUN_ID", "") if os.environ.get("GITHUB_RUN_ID") else "(local run)"
    text = (f"**Step:** {step}\n\n**Likely cause (plain English):** {plain_cause(exc)}\n\n"
            f"**Error:** `{type(exc).__name__}: {str(exc)[:500]}`\n\n**Run log:** {run}\n\n"
            "The last good projections are still the ones being served.\n\n<details><summary>Technical details</summary>\n\n"
            f"```\n{tb}\n```\n</details>\n")
    text = redact(text)
    Path(path or PROJECT_ROOT / "failure.md").write_text(text)
    return text


def redact(text: str) -> str:
    """Remove the database address and password from text that will be posted publicly."""
    import re
    from .storage import parse_db_url, read_env
    url = read_env("SUPABASE_DB_URL")
    if url:
        c = parse_db_url(url)
        for secret in sorted({url.strip(), c["password"], c["user"]} - {""}, key=len, reverse=True):
            text = text.replace(secret, "[hidden]")
    return re.sub(r"postgres(?:ql)?://\S+", "[hidden database address]", text)
