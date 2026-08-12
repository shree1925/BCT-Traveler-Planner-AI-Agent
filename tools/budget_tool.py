"""Budget estimation grounded in real hotel prices where available."""

from __future__ import annotations

from data_layer import retrieval
from utils import store
from utils.logger import get_logger

log = get_logger(__name__)

FALLBACK_NIGHTLY = {"Budget": 1500.0, "Mid-range": 4000.0, "Luxury": 12000.0}

DAILY_FOOD = {"Budget": 600.0, "Mid-range": 1500.0, "Luxury": 4000.0}
DAILY_LOCAL_TRANSPORT = {"Budget": 300.0, "Mid-range": 800.0, "Luxury": 2500.0}
DAILY_ACTIVITIES = {"Budget": 400.0, "Mid-range": 1000.0, "Luxury": 3000.0}
BUFFER_RATE = 0.10


def _normalise_style(style: str) -> str:
    text = (style or "Mid-range").strip().lower()
    if text.startswith("bud") or text.startswith("low") or text.startswith("cheap"):
        return "Budget"
    if text.startswith("lux") or text.startswith("high") or text.startswith("prem"):
        return "Luxury"
    return "Mid-range"


def estimate_budget(city: str = "", days: int = 3, travellers: int = 2, style: str = "Mid-range") -> str:
    try:
        days = max(1, int(days or 1))
        travellers = max(1, int(travellers or 1))
        style = _normalise_style(style)

        bands = retrieval.price_bands(city or None)
        if bands:
            nightly = float(bands[style])
            source = (
                f"real prices from {bands['sample_size']} hotels in "
                f"{bands['city']} (dataset quantiles)"
            )
        else:
            nightly = FALLBACK_NIGHTLY[style]
            source = "approximate national averages (no usable price column in the hotel dataset)"

        nights = max(1, days - 1) if days > 1 else 1
        rooms = max(1, (travellers + 1) // 2)

        accommodation = nightly * nights * rooms
        food = DAILY_FOOD[style] * days * travellers
        transport = DAILY_LOCAL_TRANSPORT[style] * days * travellers
        activities = DAILY_ACTIVITIES[style] * days * travellers
        subtotal = accommodation + food + transport + activities
        buffer = subtotal * BUFFER_RATE
        total = subtotal + buffer

        breakdown = {
            "city": city or "unspecified",
            "days": days,
            "nights": nights,
            "travellers": travellers,
            "rooms": rooms,
            "style": style,
            "currency": "INR",
            "nightly_rate": round(nightly),
            "accommodation_source": source,
            "items": {
                "Accommodation": round(accommodation),
                "Food": round(food),
                "Local transport": round(transport),
                "Activities": round(activities),
                "Buffer (10%)": round(buffer),
            },
            "total": round(total),
            "per_person": round(total / travellers),
            "per_person_per_day": round(total / travellers / days),
        }
        store.put("budget", breakdown)

        rows = "\n".join(f"| {k} | {v:,.0f} |" for k, v in breakdown["items"].items())
        return (
            f"Budget estimate for {travellers} traveller(s), {days} day(s) in "
            f"{city or 'the destination'} ({style}):\n\n"
            f"| Category | INR |\n|---|---|\n{rows}\n"
            f"| **Total** | **{breakdown['total']:,.0f}** |\n\n"
            f"Per person: INR {breakdown['per_person']:,.0f} "
            f"({breakdown['per_person_per_day']:,.0f} per person per day).\n"
            f"Accommodation assumes INR {breakdown['nightly_rate']:,.0f}/night x {nights} night(s) "
            f"x {rooms} room(s), based on {source}."
        )
    except Exception as exc:
        log.exception("estimate_budget failed")
        return f"Budget estimation failed: {exc}"


ESTIMATE_BUDGET_SCHEMA = {
    "name": "estimate_budget",
    "description": (
        "Estimate a trip budget in INR broken down into accommodation, food, local transport, "
        "activities and a 10% buffer. Accommodation is derived from actual hotel prices in the "
        "local dataset for that city where available. Call this whenever the user asks about "
        "cost, budget or affordability."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "Destination city."},
            "days": {"type": "integer", "description": "Trip length in days."},
            "travellers": {"type": "integer", "description": "Number of travellers."},
            "style": {
                "type": "string",
                "enum": ["Budget", "Mid-range", "Luxury"],
                "description": "Travel style.",
            },
        },
        "required": ["city", "days", "travellers", "style"],
    },
}
