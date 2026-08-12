"""Frankfurter currency conversion. Keyless."""

from __future__ import annotations

import requests

import config
from utils.logger import get_logger

log = get_logger(__name__)

FRANKFURTER_URL = "https://api.frankfurter.app/latest"


def convert_currency(amount: float, from_currency: str = "INR", to_currency: str = "USD") -> str:
    try:
        amount = float(amount)
        from_currency = (from_currency or "INR").upper().strip()
        to_currency = (to_currency or "USD").upper().strip()

        if from_currency == to_currency:
            return f"{amount:,.2f} {from_currency} = {amount:,.2f} {to_currency} (same currency)."

        response = requests.get(
            FRANKFURTER_URL,
            params={"amount": amount, "from": from_currency, "to": to_currency},
            timeout=config.HTTP_TIMEOUT,
        )
        if response.status_code == 404:
            return f"Unsupported currency code: '{from_currency}' or '{to_currency}'. Use ISO codes like INR, USD, EUR."
        response.raise_for_status()
        data = response.json() or {}
        rate = (data.get("rates") or {}).get(to_currency)
        if rate is None:
            return f"No exchange rate available for {from_currency} to {to_currency}."
        return (
            f"{amount:,.2f} {from_currency} = {float(rate):,.2f} {to_currency} "
            f"(rate date {data.get('date', 'latest')})."
        )
    except requests.RequestException as exc:
        log.warning("Currency conversion failed: %s", exc)
        return f"Currency service unreachable ({exc}). Quote prices in INR only."
    except (TypeError, ValueError) as exc:
        return f"Invalid amount for conversion: {exc}"


CONVERT_CURRENCY_SCHEMA = {
    "name": "convert_currency",
    "description": (
        "Convert an amount between two ISO 4217 currency codes using live exchange rates. "
        "Base currency for this planner is INR. Use whenever the user mentions a budget in "
        "a non-INR currency or asks what a cost is worth in their own currency."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "amount": {"type": "number", "description": "Amount to convert."},
            "from_currency": {"type": "string", "description": "Source ISO code, e.g. 'INR'."},
            "to_currency": {"type": "string", "description": "Target ISO code, e.g. 'USD'."},
        },
        "required": ["amount", "from_currency", "to_currency"],
    },
}
