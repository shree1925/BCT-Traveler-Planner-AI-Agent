"""Day-by-day itinerary composition. Pure Python orchestration.

Pulls attractions from the local dataset, checks the forecast, distributes
places across days and pushes indoor options onto high-rain days. The result
is stored for the Itinerary and Export tabs to render.
"""

from __future__ import annotations

import json
import re
from datetime import date

import pandas as pd

from data_layer import loaders, retrieval
from tools.weather_tool import WEATHER_CODES, geocode
from utils import store
from utils.helpers import date_range, parse_date, safe_float
from utils.logger import get_logger

log = get_logger(__name__)

INDOOR_HINTS = ("museum", "gallery", "palace", "temple", "church", "mosque",
                "aquarium", "planetarium", "mall", "theatre", "monument", "memorial")
OUTDOOR_HINTS = ("beach", "park", "garden", "lake", "hill", "trek", "waterfall",
                 "fort", "zoo", "safari", "island", "valley", "sunset")


def _is_indoor(text: str) -> bool:
    lowered = (text or "").lower()
    if any(h in lowered for h in OUTDOOR_HINTS):
        return False
    return any(h in lowered for h in INDOOR_HINTS)


def _attractions(city: str, limit: int) -> list[dict]:
    df = retrieval.filter_rows("destinations", city=city)
    if df.empty:
        return []
    df = retrieval.lexical_rank(df, "destinations", city, limit)

    name_col = loaders.col(df, "name")
    type_col = loaders.col(df, "type")
    fee_col = loaders.col(df, "entry_fee")
    rating_col = loaders.col(df, "rating")

    items: list[dict] = []
    for _, row in df.iterrows():
        name = str(row.get(name_col, "")).strip() if name_col else ""
        if not name or name.lower() == "nan":
            continue
        place_type = str(row.get(type_col, "")).strip() if type_col else ""
        items.append(
            {
                "name": name,
                "type": place_type,
                "entry_fee": safe_float(row.get(fee_col)) if fee_col else None,
                "rating": safe_float(row.get(rating_col)) if rating_col else None,
                "indoor": _is_indoor(f"{name} {place_type}"),
            }
        )
    return items


def _forecast_map(city: str, start: date, days: int) -> dict:
    """{iso_date: {"summary":..., "rain":...}} - empty dict on any failure."""
    try:
        import requests

        import config

        location = geocode(city)
        if not location:
            return {}
        end = start
        dates = date_range(start, days)
        end = dates[-1]
        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
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
        out = {}
        for i, day in enumerate(daily.get("time") or []):
            code = (daily.get("weather_code") or [None] * (i + 1))[i]
            tmax = (daily.get("temperature_2m_max") or [None] * (i + 1))[i]
            tmin = (daily.get("temperature_2m_min") or [None] * (i + 1))[i]
            rain = (daily.get("precipitation_probability_max") or [0] * (i + 1))[i] or 0
            out[day] = {
                "summary": f"{WEATHER_CODES.get(code, 'unknown')}, {tmin}-{tmax}C, rain {rain}%",
                "rain": float(rain),
            }
        return out
    except Exception as exc:
        log.warning("Forecast unavailable for itinerary: %s", exc)
        return {}


def build_itinerary(
    city: str,
    start_date: str = "",
    days: int = 3,
    travellers: int = 2,
    style: str = "Mid-range",
    interests: str = "",
) -> str:
    try:
        days = max(1, min(int(days or 3), 14))
        travellers = max(1, int(travellers or 1))
        start = parse_date(start_date, date.today())
        dates = date_range(start, days)

        pool = _attractions(city, days * 4)
        if not pool:
            return (
                f"The destinations dataset has no attractions for '{city}', so I cannot build a "
                f"grounded itinerary. Tell the user the dataset does not cover this city."
            )

        if interests:
            keywords = [k.strip().lower() for k in re.split(r"[,/]| and ", interests) if k.strip()]
            if keywords:
                pool.sort(
                    key=lambda p: (
                        -sum(k in f"{p['name']} {p['type']}".lower() for k in keywords),
                        -(p["rating"] or 0),
                    )
                )

        forecast = _forecast_map(city, start, days)

        indoor = [p for p in pool if p["indoor"]]
        outdoor = [p for p in pool if not p["indoor"]]

        plan = []
        for index, day_date in enumerate(dates, start=1):
            iso = day_date.isoformat()
            weather = forecast.get(iso, {})
            rainy = weather.get("rain", 0) >= 50

            primary, secondary = (indoor, outdoor) if rainy else (outdoor, indoor)
            slots = []
            for _ in range(3):
                if primary:
                    slots.append(primary.pop(0))
                elif secondary:
                    slots.append(secondary.pop(0))
            while len(slots) < 3:
                slots.append(None)

            fees = sum((s["entry_fee"] or 0) for s in slots if s)
            plan.append(
                {
                    "day": index,
                    "date": iso,
                    "weather_summary": weather.get("summary", "forecast unavailable"),
                    "rain_probability": weather.get("rain"),
                    "morning": slots[0]["name"] if slots[0] else "Free time / local exploration",
                    "afternoon": slots[1]["name"] if slots[1] else "Local market or cafe stop",
                    "evening": slots[2]["name"] if slots[2] else "Dinner and rest",
                    "notes": "Rain likely - indoor sites prioritised." if rainy else "",
                    "estimated_entry_cost_inr": round(fees * travellers),
                }
            )

        record = {
            "city": city,
            "start_date": start.isoformat(),
            "days": days,
            "travellers": travellers,
            "style": style,
            "interests": interests,
            "plan": plan,
        }
        store.put("itinerary", record)

        lines = [f"Itinerary skeleton for {city} ({days} days from {start.isoformat()}, {travellers} traveller(s)):"]
        for day in plan:
            lines.append(
                f"Day {day['day']} ({day['date']}) - {day['weather_summary']}\n"
                f"  Morning: {day['morning']}\n"
                f"  Afternoon: {day['afternoon']}\n"
                f"  Evening: {day['evening']}\n"
                f"  Entry fees approx INR {day['estimated_entry_cost_inr']:,}"
                + (f"\n  {day['notes']}" if day["notes"] else "")
            )
        lines.append(
            "This skeleton is saved to the Itinerary tab. Present it to the user as polished "
            "markdown with a header per day, adding food and transport suggestions."
        )
        return "\n".join(lines)
    except Exception as exc:
        log.exception("build_itinerary failed")
        return f"Itinerary construction failed: {exc}"


BUILD_ITINERARY_SCHEMA = {
    "name": "build_itinerary",
    "description": (
        "Build a structured day-by-day itinerary skeleton for an Indian city by combining the "
        "local attractions dataset with the live weather forecast. Indoor sites are automatically "
        "prioritised on days with a high rain probability. Call this once you know the city, "
        "start date and trip length; the result is saved for the Itinerary and Export tabs."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "Destination city."},
            "start_date": {"type": "string", "description": "Start date as YYYY-MM-DD."},
            "days": {"type": "integer", "description": "Trip length in days, 1-14."},
            "travellers": {"type": "integer", "description": "Number of travellers."},
            "style": {"type": "string", "enum": ["Budget", "Mid-range", "Luxury"]},
            "interests": {"type": "string", "description": "Comma-separated interests, e.g. 'history, food, nature'."},
        },
        "required": ["city", "days"],
    },
}
