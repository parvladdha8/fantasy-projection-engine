"""Weather forecasts for upcoming games from Open-Meteo (stored only; NOT used in projections).

Rules pre-registered in DECISIONS.md (2026-11-05, "Weather forecasts"). Open-Meteo: free for non-commercial use,
no key, data CC BY 4.0 (credit Open-Meteo on the site). One request covers every stadium.
"""

import json
import urllib.parse
import urllib.request

import pandas as pd

API = "https://api.open-meteo.com/v1/forecast"
HOURLY = ["temperature_2m", "wind_speed_10m", "wind_gusts_10m", "precipitation", "precipitation_probability", "snowfall"]
WINDOW_HOURS = 4          # kickoff hour + the next 3 hours ≈ the game
LOOKAHEAD_DAYS = 7

# nflverse stadium_id → (latitude, longitude, IANA time zone). Hand-entered; checked against Open-Meteo's own
# time zone and elevation for each point (scripts/fetch_weather.py --check).
STADIUMS = {
    "ATL97": (33.7554, -84.4008, "America/New_York"),     # Mercedes-Benz Stadium
    "BAL00": (39.2780, -76.6227, "America/New_York"),     # M&T Bank Stadium
    "BOS00": (42.0909, -71.2643, "America/New_York"),     # Gillette Stadium
    "BUF00": (42.7738, -78.7870, "America/New_York"),     # Highmark Stadium (Orchard Park)
    "CAR00": (35.2258, -80.8528, "America/New_York"),     # Bank of America Stadium
    "CHI98": (41.8623, -87.6167, "America/Chicago"),      # Soldier Field
    "CIN00": (39.0955, -84.5161, "America/New_York"),     # Paycor Stadium
    "CLE00": (41.5061, -81.6995, "America/New_York"),     # Huntington Bank Field
    "DAL00": (32.7473, -97.0945, "America/Chicago"),      # AT&T Stadium (Arlington)
    "DEN00": (39.7439, -105.0201, "America/Denver"),      # Empower Field at Mile High
    "DET00": (42.3400, -83.0456, "America/Detroit"),      # Ford Field
    "GNB00": (44.5013, -88.0622, "America/Chicago"),      # Lambeau Field
    "HOU00": (29.6847, -95.4107, "America/Chicago"),      # NRG (listed by nflverse as Reliant) Stadium
    "IND00": (39.7601, -86.1639, "America/Indiana/Indianapolis"),  # Lucas Oil Stadium
    "JAX00": (30.3239, -81.6373, "America/New_York"),     # EverBank Stadium
    "KAN00": (39.0489, -94.4839, "America/Chicago"),      # Arrowhead Stadium
    "LAX01": (33.9535, -118.3392, "America/Los_Angeles"),  # SoFi Stadium (Inglewood)
    "MAD01": (40.4531, -3.6883, "Europe/Madrid"),         # Santiago Bernabéu
    "MEX00": (19.3029, -99.1505, "America/Mexico_City"),  # Estadio Banorte (Azteca)
    "MIA00": (25.9580, -80.2389, "America/New_York"),     # Hard Rock Stadium (Miami Gardens)
    "MIN01": (44.9737, -93.2575, "America/Chicago"),      # U.S. Bank Stadium
    "MUN01": (48.2188, 11.6247, "Europe/Berlin"),         # Allianz Arena (FC Bayern Munich Stadium)
    "NAS00": (36.1665, -86.7713, "America/Chicago"),      # Nissan Stadium
    "NOR00": (29.9511, -90.0812, "America/Chicago"),      # Caesars Superdome
    "NYC01": (40.8135, -74.0745, "America/New_York"),     # MetLife Stadium (East Rutherford)
    "PHI00": (39.9008, -75.1675, "America/New_York"),     # Lincoln Financial Field
    "PHO00": (33.5276, -112.2626, "America/Phoenix"),     # State Farm Stadium (Glendale)
    "PIT00": (40.4468, -80.0158, "America/New_York"),     # Acrisure Stadium
    "SEA00": (47.5952, -122.3316, "America/Los_Angeles"),  # Lumen Field
    "SFO01": (37.4030, -121.9700, "America/Los_Angeles"),  # Levi's Stadium (Santa Clara)
    "TAM00": (27.9759, -82.5033, "America/New_York"),     # Raymond James Stadium
    "VEG00": (36.0909, -115.1833, "America/Los_Angeles"),  # Allegiant Stadium
    "WAS00": (38.9078, -76.8645, "America/New_York"),     # Northwest Stadium (Landover)
}


def upcoming_games(schedules: pd.DataFrame, kickoffs: pd.DataFrame, now: str, days: int = LOOKAHEAD_DAYS) -> pd.DataFrame:
    """Games not yet started that kick off within `days`: game_id, kickoff, stadium_id, roof."""
    end = (pd.Timestamp(now) + pd.Timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    k = kickoffs[(kickoffs["kickoff"] > now) & (kickoffs["kickoff"] <= end)]
    return k.merge(schedules[["game_id", "stadium_id", "roof"]], on="game_id", how="left")[["game_id", "kickoff", "stadium_id", "roof"]]


def request_url(stadium_ids) -> str:
    lat = ",".join(str(STADIUMS[s][0]) for s in stadium_ids)
    lon = ",".join(str(STADIUMS[s][1]) for s in stadium_ids)
    q = {"latitude": lat, "longitude": lon, "hourly": ",".join(HOURLY), "temperature_unit": "fahrenheit",
         "wind_speed_unit": "mph", "precipitation_unit": "mm", "timezone": "auto", "timeformat": "unixtime",
         "forecast_days": LOOKAHEAD_DAYS + 1}
    return API + "?" + urllib.parse.urlencode(q, safe=",")


def fetch(stadium_ids, timeout: int = 30) -> list[dict]:
    """One Open-Meteo request for all stadiums; returns one response object per stadium, in order."""
    with urllib.request.urlopen(urllib.request.Request(request_url(stadium_ids), headers={"User-Agent": "fantasy-projection-engine (non-commercial research)"}),
                                timeout=timeout) as r:
        data = json.load(r)
    return data if isinstance(data, list) else [data]


def game_window(resp: dict, kickoff: str) -> dict | None:
    """Aggregate the hourly forecast over the game window (kickoff hour + 3). None if the window isn't covered."""
    h = pd.DataFrame(resp["hourly"])
    h["t"] = pd.to_datetime(h["time"], unit="s", utc=True)
    start = pd.Timestamp(kickoff).floor("h")
    w = h[(h["t"] >= start) & (h["t"] < start + pd.Timedelta(hours=WINDOW_HOURS))]
    if len(w) < WINDOW_HOURS or w["temperature_2m"].isna().all():
        return None
    return {"temp_f": float(w["temperature_2m"].mean()), "wind_mph": float(w["wind_speed_10m"].mean()),
            "gust_mph": float(w["wind_gusts_10m"].max()), "precip_mm": float(w["precipitation"].sum()),
            "precip_prob": None if w["precipitation_probability"].isna().all() else float(w["precipitation_probability"].max()),
            "snow_cm": float(w["snowfall"].sum())}


def forecasts(games: pd.DataFrame, responses: dict, fetched_at: str) -> tuple[pd.DataFrame, list[str]]:
    """Rows for weather_forecasts. responses: stadium_id → Open-Meteo object. Returns (rows, notes on skipped games)."""
    rows, notes = [], []
    for g in games.itertuples():
        if g.stadium_id not in responses:
            notes.append(f"{g.game_id}: no coordinates for stadium {g.stadium_id}; skipped")
            continue
        r = responses[g.stadium_id]
        w = game_window(r, g.kickoff)
        if w is None:
            notes.append(f"{g.game_id}: forecast does not cover kickoff {g.kickoff}; skipped")
            continue
        rows.append({"game_id": g.game_id, "fetched_at": fetched_at, "kickoff": g.kickoff, "stadium_id": g.stadium_id,
                     "roof": None if pd.isna(g.roof) else g.roof, "latitude": STADIUMS[g.stadium_id][0],
                     "longitude": STADIUMS[g.stadium_id][1], **w, "source": "open-meteo"})
    return pd.DataFrame(rows), notes
