"""Download and cache raw nflverse data.

Plain English: this file fetches the free nflverse data once and saves it to
`data/raw/` as Parquet files (a compact table format). Everything else reads the
saved copy, so we don't re-download on every run and results are reproducible.
"""

from pathlib import Path

import nflreadpy as nfl
import pandas as pd

from . import SEASONS

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
LIVE_DIR = PROJECT_ROOT / "data" / "live"
LIVE_TABLES = ["player_stats_week", "schedules", "snap_counts", "injuries", "players", "rosters_weekly", "rosters"]


def pull_raw(seasons: list[int] = SEASONS) -> dict[str, Path]:
    """Download weekly player stats + schedules and save them. Returns file paths."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    paths = {
        "player_stats": RAW_DIR / "player_stats_week.parquet",
        "schedules": RAW_DIR / "schedules.parquet",
        "snap_counts": RAW_DIR / "snap_counts.parquet",
        "players": RAW_DIR / "players.parquet",
    }
    nfl.load_player_stats(seasons, summary_level="week").write_parquet(paths["player_stats"])
    nfl.load_schedules(seasons).write_parquet(paths["schedules"])
    nfl.load_snap_counts(seasons).write_parquet(paths["snap_counts"])
    nfl.load_players().write_parquet(paths["players"])  # ID crosswalk (gsis <-> pfr)
    return paths


def pull_injuries(seasons: list[int] = SEASONS) -> Path:
    """Download weekly injury reports (practice status + game designation). Separate from pull_raw
    so adding it doesn't re-download (and possibly change) the data earlier results were built on."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / "injuries.parquet"
    nfl.load_injuries(seasons).write_parquet(path)
    return path


def load_injuries() -> pd.DataFrame:
    return pd.read_parquet(RAW_DIR / "injuries.parquet")


def load_rosters_weekly() -> pd.DataFrame:
    """Frozen 2018–25 weekly rosters (team per player per week). Added 2026-11-03 as a new file."""
    return pd.read_parquet(RAW_DIR / "rosters_weekly.parquet")


def load_player_stats() -> pd.DataFrame:
    return pd.read_parquet(RAW_DIR / "player_stats_week.parquet")


def load_schedules() -> pd.DataFrame:
    return pd.read_parquet(RAW_DIR / "schedules.parquet")


def load_snap_counts() -> pd.DataFrame:
    return pd.read_parquet(RAW_DIR / "snap_counts.parquet")


def load_players() -> pd.DataFrame:
    return pd.read_parquet(RAW_DIR / "players.parquet")


def pull_live(season: int, stamp: str | None = None) -> Path:
    """Download the in-progress season into its OWN timestamped folder, data/live/<season>/<UTC stamp>/.
    The frozen 2018–2025 files in data/raw/ (behind every committed result) are never touched, and every
    pull is kept, so we can later show exactly what data a projection was made from."""
    from datetime import datetime, timezone
    stamp = stamp or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = LIVE_DIR / str(season) / stamp
    out.mkdir(parents=True, exist_ok=False)
    nfl.load_player_stats([season], summary_level="week").write_parquet(out / "player_stats_week.parquet")
    nfl.load_schedules([season]).write_parquet(out / "schedules.parquet")
    nfl.load_snap_counts([season]).write_parquet(out / "snap_counts.parquet")
    nfl.load_injuries([season]).write_parquet(out / "injuries.parquet")
    nfl.load_players().write_parquet(out / "players.parquet")  # refreshed crosswalk (includes rookies)
    nfl.load_rosters_weekly([season]).write_parquet(out / "rosters_weekly.parquet")
    nfl.load_rosters([season]).write_parquet(out / "rosters.parquet")  # current roster AS OF this pull (pre-game)
    return out


def latest_live(season: int) -> Path:
    """Most recent complete live pull for a season."""
    pulls = sorted(p for p in (LIVE_DIR / str(season)).glob("*") if all((p / f"{t}.parquet").exists() for t in LIVE_TABLES))
    if not pulls:
        raise FileNotFoundError(f"no complete live pull for {season} under {LIVE_DIR}")
    return pulls[-1]


def load_live(season: int, table: str, pull: Path | None = None) -> pd.DataFrame:
    return pd.read_parquet((pull or latest_live(season)) / f"{table}.parquet")
