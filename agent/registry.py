"""Single source of truth: tool name -> (JSON schema, python callable)."""

from __future__ import annotations

from typing import Callable

from tools import budget_tool, currency_tool, dataset_tools, email_tool, itinerary_tool
from tools import pdf_tool, places_tool, weather_tool

TOOLS: dict[str, tuple[dict, Callable]] = {
    dataset_tools.CHECK_CITY_COVERAGE_SCHEMA["name"]: (
        dataset_tools.CHECK_CITY_COVERAGE_SCHEMA, dataset_tools.check_city_coverage),
    dataset_tools.SEARCH_DESTINATIONS_SCHEMA["name"]: (
        dataset_tools.SEARCH_DESTINATIONS_SCHEMA, dataset_tools.search_destinations),
    dataset_tools.SEARCH_HOTELS_SCHEMA["name"]: (
        dataset_tools.SEARCH_HOTELS_SCHEMA, dataset_tools.search_hotels),
    dataset_tools.GET_REFERENCE_ITINERARY_SCHEMA["name"]: (
        dataset_tools.GET_REFERENCE_ITINERARY_SCHEMA, dataset_tools.get_reference_itinerary),

    
    weather_tool.GET_WEATHER_FORECAST_SCHEMA["name"]: (
        weather_tool.GET_WEATHER_FORECAST_SCHEMA, weather_tool.get_weather_forecast),
    places_tool.SEARCH_PLACES_SCHEMA["name"]: (
        places_tool.SEARCH_PLACES_SCHEMA, places_tool.search_places),
    currency_tool.CONVERT_CURRENCY_SCHEMA["name"]: (
        currency_tool.CONVERT_CURRENCY_SCHEMA, currency_tool.convert_currency),

    
    budget_tool.ESTIMATE_BUDGET_SCHEMA["name"]: (
        budget_tool.ESTIMATE_BUDGET_SCHEMA, budget_tool.estimate_budget),
    itinerary_tool.BUILD_ITINERARY_SCHEMA["name"]: (
        itinerary_tool.BUILD_ITINERARY_SCHEMA, itinerary_tool.build_itinerary),
    pdf_tool.EXPORT_ITINERARY_PDF_SCHEMA["name"]: (
        pdf_tool.EXPORT_ITINERARY_PDF_SCHEMA, pdf_tool.export_itinerary_pdf),
    email_tool.SEND_ITINERARY_EMAIL_SCHEMA["name"]: (
        email_tool.SEND_ITINERARY_EMAIL_SCHEMA, email_tool.send_itinerary_email),
}

TOOL_SCHEMAS: list[dict] = [schema for schema, _ in TOOLS.values()]


SPINNER_COPY = {
    "check_city_coverage": "Checking the map...",
    "search_destinations": "Leafing through the guidebook...",
    "search_hotels": "Knocking on hotel doors...",
    "get_reference_itinerary": "Borrowing a proven route...",
    "get_weather_forecast": "Checking the skies...",
    "search_places": "Asking a local...",
    "convert_currency": "Counting the change...",
    "estimate_budget": "Doing the sums...",
    "build_itinerary": "Packing your itinerary...",
    "export_itinerary_pdf": "Printing your plan...",
    "send_itinerary_email": "Licking the stamp...",
}


def get_callable(name: str):
    entry = TOOLS.get(name)
    return entry[1] if entry else None
