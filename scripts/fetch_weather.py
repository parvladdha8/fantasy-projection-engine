"""Fetch Open-Meteo forecasts for games in the next 7 days and append them to weather_forecasts (stored only).

Usage:
  uv run python scripts/fetch_weather.py --check          # verify stadium table (time zone + elevation); writes nothing
  uv run python scripts/fetch_weather.py                  # Supabase
  uv run python scripts/fetch_weather.py --sqlite PATH    # local SQLite file
Weather data by Open-Meteo.com (CC BY 4.0).
"""

import sys

import nflreadpy as nfl

from fantasy_projection_engine import LIVE_SEASON
from fantasy_projection_engine.alerts import write_failure
from fantasy_projection_engine.data import latest_live, load_live
from fantasy_projection_engine.live import kickoffs
from fantasy_projection_engine.storage import connect_postgres, connect_sqlite, save_weather, utc_now
from fantasy_projection_engine.weather import STADIUMS, fetch, forecasts, upcoming_games

# Rough elevation (m) expected for the high/low-altitude sites; everything else should be below 400 m.
HIGH = {"DEN00": (1500, 1700), "MEX00": (2150, 2350), "PHO00": (300, 400), "VEG00": (600, 700), "MUN01": (480, 560),
        "MAD01": (620, 720)}


def check():
    ids = list(STADIUMS)
    bad = 0
    for sid, r in zip(ids, fetch(ids)):
        tz, elev = r.get("timezone"), r.get("elevation")
        lo, hi = HIGH.get(sid, (-10, 400))
        ok = tz == STADIUMS[sid][2] and lo <= elev <= hi
        bad += not ok
        print(f"{'ok ' if ok else 'BAD'} {sid}: time zone {tz} (expected {STADIUMS[sid][2]}), elevation {elev:.0f} m "
              f"(expected {lo}–{hi})")
    print(f"\n{len(ids) - bad} of {len(ids)} stadiums pass")
    return bad == 0


def main(argv):
    if "--check" in argv:
        raise SystemExit(0 if check() else 1)
    now = utc_now()
    try:   # reuse the schedule the refresh just downloaded (same run on GitHub); download only if there is none
        sched = load_live(LIVE_SEASON, "schedules", latest_live(LIVE_SEASON))
    except FileNotFoundError:
        sched = nfl.load_schedules([LIVE_SEASON]).to_pandas()
    games = upcoming_games(sched, kickoffs(sched, LIVE_SEASON), now)
    ids = sorted(set(games["stadium_id"].dropna()) & set(STADIUMS))
    responses = dict(zip(ids, fetch(ids))) if ids else {}
    rows, notes = forecasts(games, responses, fetched_at=now)
    conn = connect_sqlite(argv[argv.index("--sqlite") + 1]) if "--sqlite" in argv else connect_postgres()
    n = save_weather(conn, rows)
    conn.close()
    print(f"{now}: {len(games)} games in the next 7 days; forecasts stored for {n} (one request, {len(ids)} stadiums)")
    for x in notes:
        print("  note:", x)
    if n:
        show = rows.sort_values("kickoff")[["game_id", "roof", "temp_f", "wind_mph", "gust_mph", "precip_mm", "precip_prob"]]
        print(show.round(1).to_string(index=False))


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except SystemExit:
        raise
    except Exception as e:
        print(write_failure("weather forecast (Open-Meteo; projections unaffected)", e))
        raise SystemExit(1)
