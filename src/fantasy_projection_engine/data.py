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


def pull_raw(seasons: list[int] = SEASONS) -> dict[str, Path]:
    """Download weekly player stats + schedules and save them. Returns file paths."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    paths = {
        "player_stats": RAW_DIR / "player_stats_week.parquet",
        "schedules": RAW_DIR / "schedules.parquet",
    }
    nfl.load_player_stats(seasons, summary_level="week").write_parquet(paths["player_stats"])
    nfl.load_schedules(seasons).write_parquet(paths["schedules"])
    return paths


def load_player_stats() -> pd.DataFrame:
    return pd.read_parquet(RAW_DIR / "player_stats_week.parquet")


def load_schedules() -> pd.DataFrame:
    return pd.read_parquet(RAW_DIR / "schedules.parquet")
