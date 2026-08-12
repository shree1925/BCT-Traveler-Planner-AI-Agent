"""Open-Meteo weather + geocoding. Keyless."""

from __future__ import annotations

from datetime import date, timedelta

import requests

import config
from utils.helpers import parse_date
from utils.logger import get_logger

log = get_logger(__name__)

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

WEATHER_CODES = {
    0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
    45: "fog", 48: "rime fog", 51: "light drizzle", 53: "drizzle",
    55: "heavy drizzle", 61: "light rain", 63: "rain", 65: "heavy rain",
    71: "light snow", 73: "snow", 75: "heavy snow", 80: "rain showers",
    81: "heavy showers", 82: "violent showers", 95: "thunderstorm",
    96: "thunderstorm with hail", 99: "severe thunderstorm with hail",
}


def geocode(city: str) -> dict | None:
    try:
        response = requests.get(
            GEOCODE_URL,
            params={"name": city, "count": 1, "language": "en", "format": "json"},
            timeout=config.HTTP_TIMEOUT,
        )
        response.raise_for_status()
        results = (response.json() or {}).get("results") or []
        if not results:
            return None
        top = results[0]
        return {
            "name": top.get("name"),
            "country": top.get("country"),
            "admin1": top.get("admin1"),
            "latitude": top.get("latitude"),
            "longitude": top.get("longitude"),
        }
    except requests.RequestException as exc:
        log.warning("Geocoding failed for %s: %s", city, exc)
        return None


def get_weather_forecast(city: str, start_date: str = "", days: int = 5) -> str:
    try:
        location = geocode(city)
        if not location:
            return f"Could not geocode '{city}'. Ask the user to confirm the city name."

        start = parse_date(start_date, date.today())
        days = max(1, min(int(days or 5), 16))

        today = date.today()
        note = ""
        if start < today:
            note = f" (requested start {start} is in the past; showing from today)"
            start = today
        max_end = today + timedelta(days=15)
        end = start + timedelta(days=days - 1)
        if end > max_end:
            end = max_end
            note += " (Open-Meteo forecasts only 16 days ahead; range truncated)"
        if start > max_end:
            return (
                f"{city}: the trip starts more than 16 days out, so no forecast is available yet. "
                f"Use seasonal 'best time to visit' guidance from the destinations dataset instead."
            )

        response = requests.get(
            FORECAST_URL,
            params={
                "latitude": location["latitude"],
                "longitude": location["longitude"],
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                "timezone": "auto",
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
            },
            timeout=config.HTTP_TIMEOUT,
        )
        response.raise_for_status()
        daily = (response.json() or {}).get("daily") or {}
        dates = daily.get("time") or []
        if not dates:
            return f"No forecast data returned for {city}."

        lines = [f"Weather forecast for {location['name']}, {location.get('admin1') or ''}{note}".strip()]
        for i, day in enumerate(dates):
            code = (daily.get("weather_code") or [None])[i] if i < len(daily.get("weather_code", [])) else None
            tmax = (daily.get("temperature_2m_max") or [None])[i] if i < len(daily.get("temperature_2m_max", [])) else None
            tmin = (daily.get("temperature_2m_min") or [None])[i] if i < len(daily.get("temperature_2m_min", [])) else None
            rain = (daily.get("precipitation_probability_max") or [None])[i] if i < len(daily.get("precipitation_probability_max", [])) else None
            lines.append(
                f"- {day}: {WEATHER_CODES.get(code, 'unknown')}, "
                f"{tmin}C to {tmax}C, rain chance {rain}%"
            )
        lines.append("Days with rain chance above 50% should favour indoor activities.")
        return "\n".join(lines)
    except requests.RequestException as exc:
        log.warning("Forecast failed for %s: %s", city, exc)
        return f"Weather service unreachable for {city} ({exc}). Plan without forecast data and say so."
    except Exception as exc:
        log.exception("get_weather_forecast failed")
        return f"Weather lookup failed: {exc}"


GET_WEATHER_FORECAST_SCHEMA = {
    "name": "get_weather_forecast",
    "description": (
        "Get the daily weather forecast for a city: condition, max/min temperature in Celsius "
        "and rain probability. Call this BEFORE recommending any outdoor activity. Forecasts "
        "are only available up to 16 days ahead."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "City name, e.g. 'Udaipur'."},
            "start_date": {"type": "string", "description": "Trip start date as YYYY-MM-DD. Defaults to today."},
            "days": {"type": "integer", "description": "Number of days to forecast, 1-16."},
        },
        "required": ["city"],
    },
}
