"""Download the live (in-progress) season into data/live/<season>/<UTC stamp>/ and print a data-quality report.

Usage: uv run python scripts/pull_live.py [season]   (default: LIVE_SEASON)
"""

import sys

from fantasy_projection_engine import LIVE_SEASON
from fantasy_projection_engine.data import load_live, pull_live

season = int(sys.argv[1]) if len(sys.argv) > 1 else LIVE_SEASON
out = pull_live(season)
print("saved to", out)
s = load_live(season, "schedules", out)
reg = s[s.game_type == "REG"]
played = reg.home_score.notna()
up = reg[~played]
print(f"\nschedule: {len(reg)} regular-season games, {played.sum()} played, {len(up)} upcoming")
print("played through week:", int(reg.loc[played, "week"].max()) if played.any() else None)
if len(up):
    nxt = up[up.week == up.week.min()]
    print(f"next week {int(nxt.week.min())}: {len(nxt)} games; with spread & total: "
          f"{nxt[['spread_line', 'total_line']].notna().all(axis=1).sum()}; with gametime: {nxt.gametime.notna().sum()}; "
          f"with temp/wind: {nxt[['temp', 'wind']].notna().all(axis=1).sum()}")
    later = up[up.week > up.week.min()]
    print(f"later weeks: {len(later)} games; with spread & total: {later[['spread_line', 'total_line']].notna().all(axis=1).sum()}")
ps = load_live(season, "player_stats_week", out)
print(f"\nplayer stats: {len(ps)} rows, weeks {sorted(ps.week.unique().tolist())}, season_type {ps.season_type.unique().tolist()}")
sc = load_live(season, "snap_counts", out)
print(f"snap counts: {len(sc)} rows, weeks {sorted(sc.week.unique().tolist())}")
inj = load_live(season, "injuries", out)
print(f"injuries: {len(inj)} rows, weeks {sorted(inj.week.unique().tolist())}")
print(f"players: {len(load_live(season, 'players', out))} rows")
