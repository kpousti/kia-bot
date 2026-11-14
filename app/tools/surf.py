"""Surf tool: La Jolla Shores waves, wind, and tides from free public APIs (no keys needed)."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import httpx

TZ = ZoneInfo("America/Los_Angeles")
LAT, LON = 32.857, -117.257   # La Jolla Shores
NOAA_STATION = "9410230"      # Scripps Pier tide gauge, La Jolla

TOOL_SPEC = {
    "name": "get_surf_forecast",
    "description": (
        "Get the surf forecast for La Jolla Shores: hourly wave height (ft), swell period (s), "
        "wind speed/direction, and high/low tide times. Use for any surf, beach, wave, or tide question."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "days": {"type": "integer", "minimum": 1, "maximum": 3, "description": "How many days to fetch, counting today as day 1: 1 = today only, 2 = today and tomorrow, 3 = through the day after. Use 2 or more for any question about tomorrow. Default 2."}
        },
    },
}

M_TO_FT = 3.281
KMH_TO_MPH = 0.6214


def _fetch_waves(days: int) -> dict:
    # Open-Meteo marine API: waves + swell
    r = httpx.get("https://marine-api.open-meteo.com/v1/marine", params={
        "latitude": LAT, "longitude": LON, "timezone": "America/Los_Angeles", "forecast_days": days,
        "hourly": "wave_height,swell_wave_height,swell_wave_period,swell_wave_direction",
    }, timeout=10)
    r.raise_for_status()
    return r.json()["hourly"]


def _fetch_wind(days: int) -> dict:
    # Open-Meteo weather API: wind matters most for surf quality (offshore = clean)
    r = httpx.get("https://api.open-meteo.com/v1/forecast", params={
        "latitude": LAT, "longitude": LON, "timezone": "America/Los_Angeles", "forecast_days": days,
        "hourly": "wind_speed_10m,wind_direction_10m,temperature_2m",
    }, timeout=10)
    r.raise_for_status()
    return r.json()["hourly"]


def _fetch_tides(days: int) -> list[dict]:
    # NOAA CO-OPS predictions, high/low only
    start = datetime.now(TZ)
    r = httpx.get("https://api.tidesandcurrents.noaa.gov/api/prod/datagetter", params={
        "station": NOAA_STATION, "product": "predictions", "datum": "MLLW", "interval": "hilo",
        "units": "english", "time_zone": "lst_ldt", "format": "json",
        "begin_date": start.strftime("%Y%m%d"),
        "end_date": (start + timedelta(days=days - 1)).strftime("%Y%m%d"),
    }, timeout=10)
    r.raise_for_status()
    return [{"time": p["t"], "type": "high" if p["type"] == "H" else "low", "ft": round(float(p["v"]), 1)}
            for p in r.json().get("predictions", [])]


def _offshore(deg: float) -> bool:
    # La Jolla Shores faces west, so east-ish winds (45-135 deg) blow offshore
    return 45 <= deg <= 135


def run(days: int = 2) -> dict:
    days = max(1, min(3, int(days)))  # clamp to what the APIs and voice answers can handle
    waves, wind = _fetch_waves(days), _fetch_wind(days)
    hours = []
    # Keep daylight hours only (5am-7pm) so the summary stays short for voice
    for i, t in enumerate(waves["time"]):
        hour = int(t[11:13])
        if not 5 <= hour <= 19 or i % 2:  # every 2 hours is enough detail
            continue
        if i >= len(wind["wind_speed_10m"]):  # the two APIs should line up; stop if they don't
            break
        height, speed = waves["wave_height"][i], wind["wind_speed_10m"][i]
        wdir, temp = wind["wind_direction_10m"][i], wind["temperature_2m"][i]
        # Live data can have null hours; pass None through rather than crash or invent a number
        hours.append({
            "time": t,
            "wave_ft": None if height is None else round(height * M_TO_FT, 1),
            "swell_period_s": waves["swell_wave_period"][i],
            "wind_mph": None if speed is None else round(speed * KMH_TO_MPH),
            "wind": None if wdir is None else ("offshore" if _offshore(wdir) else "onshore/cross"),
            "air_f": None if temp is None else round(temp * 9 / 5 + 32),
        })
    try:
        tides = _fetch_tides(days)
    except httpx.HTTPError:
        tides = []  # tides are a nice-to-have; don't fail the whole answer
    return {"spot": "La Jolla Shores", "hourly": hours, "tides": tides,
            "note": "Best conditions: wind under ~8 mph or offshore, swell period 10s+."}
