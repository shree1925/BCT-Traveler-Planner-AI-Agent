"""Tools that read the local CSVs - the 'inside data' half of the agent."""

from __future__ import annotations

import config
from data_layer import loaders, retrieval
from utils.logger import get_logger

log = get_logger(__name__)


def search_destinations(
    city: str = "",
    query: str = "",
    state: str = "",
    place_type: str = "",
    min_rating: float | None = None,
    top_k: int = config.DEFAULT_TOP_K,
) -> str:
    try:
        return retrieval.search(
            "destinations",
            query=query or place_type or city,
            fields=["name", "city", "state", "type", "rating", "entry_fee", "best_time", "time_needed", "description"],
            top_k=int(top_k or config.DEFAULT_TOP_K),
            city=city or None,
            state=state or None,
            place_type=place_type or None,
            min_rating=min_rating,
        )
    except Exception as exc:  
        log.exception("search_destinations failed")
        return f"Destination lookup failed: {exc}"


SEARCH_DESTINATIONS_SCHEMA = {
    "name": "search_destinations",
    "description": (
        "Search the local Indian tourist-attraction dataset for places to visit. "
        "Use this BEFORE stating any fact about an attraction. Returns name, city, "
        "type, Google rating, entrance fee in INR, best time to visit and hours needed. "
        "Filter by city for best results."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "City name, e.g. 'Jaipur'. Strongly recommended."},
            "query": {"type": "string", "description": "Free-text interest, e.g. 'fort palace history' or 'beach sunset'."},
            "state": {"type": "string", "description": "Indian state, e.g. 'Rajasthan'. Optional."},
            "place_type": {"type": "string", "description": "Attraction category, e.g. 'Temple', 'Fort', 'Beach', 'Museum'."},
            "min_rating": {"type": "number", "description": "Minimum Google review rating, 0-5."},
            "top_k": {"type": "integer", "description": "How many results to return (default 5)."},
        },
        "required": [],
    },
}


def search_hotels(
    city: str = "",
    query: str = "",
    style: str = "",
    max_price: float | None = None,
    top_k: int = config.DEFAULT_TOP_K,
) -> str:
    try:
        min_price = None
        if style and max_price is None:
            bands = retrieval.price_bands(city or None)
            if bands:
                if style.lower().startswith("budget"):
                    max_price = bands["Mid-range"]
                elif style.lower().startswith("lux"):
                    min_price = bands["Mid-range"]
                else:
                    min_price = bands["Budget"] * 0.8
                    max_price = bands["Luxury"]

        return retrieval.search(
            "hotels",
            query=query or style,
            fields=["name", "city", "area", "type", "star_rating", "rating", "price", "amenities"],
            top_k=int(top_k or config.DEFAULT_TOP_K),
            city=city or None,
            min_price=min_price,
            max_price=max_price,
        )
    except Exception as exc:
        log.exception("search_hotels failed")
        return f"Hotel lookup failed: {exc}"


SEARCH_HOTELS_SCHEMA = {
    "name": "search_hotels",
    "description": (
        "Search the local hotel dataset for accommodation in an Indian city. "
        "Returns property name, area, type, star rating, review rating, nightly price "
        "in INR where available, and key amenities. Use this for every accommodation "
        "recommendation instead of naming hotels from memory."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "City name, e.g. 'Goa'. Strongly recommended."},
            "query": {"type": "string", "description": "Free-text requirement, e.g. 'pool wifi family friendly'."},
            "style": {
                "type": "string",
                "enum": ["Budget", "Mid-range", "Luxury"],
                "description": "Price tier. Bands are computed from real prices in the dataset.",
            },
            "max_price": {"type": "number", "description": "Hard nightly price ceiling in INR."},
            "top_k": {"type": "integer", "description": "How many results (default 5)."},
        },
        "required": [],
    },
}


def get_reference_itinerary(city: str = "", days: int | None = None, query: str = "") -> str:
    try:
        result = retrieval.search(
            "itineraries",
            query=query,
            fields=["city", "state", "day", "activity", "category", "duration", "cost", "description"],
            top_k=max(6, int(days or 3) * 3),
            city=city or None,
        )
        if days:
            result = f"(User is planning {days} days - adapt this reference plan.)\n" + result
        return result
    except Exception as exc:
        log.exception("get_reference_itinerary failed")
        return f"Reference itinerary lookup failed: {exc}"


GET_REFERENCE_ITINERARY_SCHEMA = {
    "name": "get_reference_itinerary",
    "description": (
        "Fetch existing day-wise reference itineraries for an Indian city from the local "
        "itinerary dataset. Use this as a skeleton to adapt rather than inventing a plan "
        "from scratch."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "City name."},
            "days": {"type": "integer", "description": "Number of days the user is planning."},
            "query": {"type": "string", "description": "Optional interest filter, e.g. 'heritage food'."},
        },
        "required": ["city"],
    },
}


def check_city_coverage(city: str) -> str:
    """Tell the agent honestly whether the datasets cover a city at all."""
    try:
        lines = [f"Coverage check for '{city}':"]
        any_hit = False
        for dataset in ("destinations", "hotels", "itineraries", "cities"):
            if loaders.load(dataset).empty:
                lines.append(f"- {dataset}: dataset file not loaded")
                continue
            count = len(retrieval.filter_rows(dataset, city=city))
            total = len(loaders.load(dataset))
            if count and count != total:
                any_hit = True
                lines.append(f"- {dataset}: {count} matching rows")
            else:
                lines.append(f"- {dataset}: no rows for this city")
        if not any_hit:
            lines.append(
                "VERDICT: this city is NOT covered by the local datasets. Tell the user plainly, "
                "then offer to plan using live APIs only, clearly labelled as ungrounded."
            )
        else:
            lines.append("VERDICT: covered - use the dataset tools.")
        return "\n".join(lines)
    except Exception as exc:
        log.exception("check_city_coverage failed")
        return f"Coverage check failed: {exc}"


CHECK_CITY_COVERAGE_SCHEMA = {
    "name": "check_city_coverage",
    "description": (
        "Check whether the local datasets contain any records for a city before planning. "
        "Call this first when the user names an unfamiliar destination so you never invent "
        "records for a city the data does not cover."
    ),
    "parameters": {
        "type": "object",
        "properties": {"city": {"type": "string", "description": "City name to check."}},
        "required": ["city"],
    },
}
