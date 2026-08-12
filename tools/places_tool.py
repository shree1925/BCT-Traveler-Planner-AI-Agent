"""OpenStreetMap Nominatim POI search - the 'outside data' complement to the CSVs.

Nominatim's usage policy requires a descriptive User-Agent and a maximum of
one request per second. Both are enforced here.
"""

from __future__ import annotations

import threading
import time

import requests

import config
from utils.logger import get_logger

log = get_logger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

_lock = threading.Lock()
_last_call = [0.0]


def _rate_limit() -> None:
    with _lock:
        elapsed = time.time() - _last_call[0]
        if elapsed < 1.05:
            time.sleep(1.05 - elapsed)
        _last_call[0] = time.time()


def search_places(query: str, city: str = "", limit: int = 5) -> str:
    try:
        limit = max(1, min(int(limit or 5), 10))
        search_text = f"{query} in {city}, India" if city else f"{query}, India"

        _rate_limit()
        response = requests.get(
            NOMINATIM_URL,
            params={"q": search_text, "format": "json", "limit": limit, "addressdetails": 1},
            headers={"User-Agent": config.NOMINATIM_USER_AGENT, "Accept-Language": "en"},
            timeout=config.HTTP_TIMEOUT,
        )
        response.raise_for_status()
        results = response.json() or []
        if not results:
            return f"No OpenStreetMap results for '{search_text}'."

        lines = [f"OpenStreetMap results for '{search_text}' (live, not from the local dataset):"]
        for i, item in enumerate(results, start=1):
            name = item.get("display_name", "").split(",")[0]
            category = f"{item.get('class', '')}/{item.get('type', '')}".strip("/")
            address = item.get("display_name", "")
            if len(address) > 140:
                address = address[:140] + "..."
            lines.append(
                f"{i}. {name} | category: {category or 'n/a'} | "
                f"lat/lon: {item.get('lat')},{item.get('lon')} | {address}"
            )
        return "\n".join(lines)
    except requests.RequestException as exc:
        log.warning("Nominatim failed: %s", exc)
        return f"Places service unreachable ({exc}). Rely on the local destinations dataset instead."
    except Exception as exc:
        log.exception("search_places failed")
        return f"Places lookup failed: {exc}"


SEARCH_PLACES_SCHEMA = {
    "name": "search_places",
    "description": (
        "Look up live points of interest (restaurants, cafes, parks, stations, landmarks) "
        "from OpenStreetMap. This is LIVE data, not the curated local dataset - use it to "
        "supplement search_destinations for practical spots like food and transport, not as "
        "the primary source for attractions."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "What to look for, e.g. 'vegetarian restaurant', 'railway station'."},
            "city": {"type": "string", "description": "City to search within."},
            "limit": {"type": "integer", "description": "Number of results, 1-10."},
        },
        "required": ["query"],
    },
}
