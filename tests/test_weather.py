"""Tests for weather forecasts (made-up Open-Meteo responses; no network)."""

import pandas as pd
import pytest

from fantasy_projection_engine.storage import connect_sqlite, save_weather
from fantasy_projection_engine.weather import STADIUMS, forecasts, game_window, request_url, upcoming_games


def _resp(start="2026-11-08T12:00:00Z", hours=12, temp=30.0, wind=10.0):
    t0 = int(pd.Timestamp(start).timestamp())
    t = [t0 + 3600 * i for i in range(hours)]
    return {"hourly": {"time": t, "temperature_2m": [temp + i for i in range(hours)], "wind_speed_10m": [wind] * hours,
                       "wind_gusts_10m": [wind + i for i in range(hours)], "precipitation": [0.5] * hours,
                       "precipitation_probability": [10 * i for i in range(hours)], "snowfall": [0.0] * hours}}


def test_game_window_is_kickoff_hour_plus_three():
    w = game_window(_resp(), "2026-11-08T18:25:00Z")      # kickoff 18:25 → hours 18, 19, 20, 21 (index 6–9)
    assert w["temp_f"] == pytest.approx(30 + 7.5)
    assert w["gust_mph"] == 10 + 9 and w["precip_mm"] == pytest.approx(2.0) and w["precip_prob"] == 90


def test_window_outside_forecast_is_skipped():
    assert game_window(_resp(hours=8), "2026-11-08T18:00:00Z") is None


def test_upcoming_only_future_games_within_a_week():
    k = pd.DataFrame({"game_id": ["past", "soon", "far"], "week": 9,
                      "kickoff": ["2026-11-05T01:00:00Z", "2026-11-08T18:00:00Z", "2026-11-20T18:00:00Z"]})
    s = pd.DataFrame({"game_id": ["past", "soon", "far"], "stadium_id": "GNB00", "roof": "outdoors"})
    assert upcoming_games(s, k, "2026-11-05T12:00:00Z")["game_id"].tolist() == ["soon"]


def test_unknown_stadium_is_logged_not_fatal_and_rows_append():
    games = pd.DataFrame({"game_id": ["a", "b"], "kickoff": "2026-11-08T18:00:00Z", "stadium_id": ["GNB00", "LON99"],
                          "roof": ["outdoors", None]})
    rows, notes = forecasts(games, {"GNB00": _resp()}, fetched_at="2026-11-05T12:00:00Z")
    assert rows["game_id"].tolist() == ["a"] and "LON99" in notes[0]
    c = connect_sqlite()
    assert save_weather(c, rows) == 1
    assert save_weather(c, rows.assign(fetched_at="2026-11-06T12:00:00Z")) == 1   # a later fetch is a new row
    assert c.execute("SELECT COUNT(*) FROM weather_forecasts").fetchone()[0] == 2


def test_forecast_fetched_after_kickoff_is_refused():
    games = pd.DataFrame({"game_id": ["a"], "kickoff": "2026-11-08T18:00:00Z", "stadium_id": ["GNB00"], "roof": ["outdoors"]})
    rows, _ = forecasts(games, {"GNB00": _resp()}, fetched_at="2026-11-08T19:00:00Z")
    with pytest.raises(Exception):
        save_weather(connect_sqlite(), rows)


def test_request_covers_all_stadiums_in_one_call():
    url = request_url(list(STADIUMS))
    assert url.count(",") >= 2 * (len(STADIUMS) - 1) and "timeformat=unixtime" in url and "temperature_unit=fahrenheit" in url
