"""Shared text / date / formatting helpers. Stdlib + pandas only."""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta

_TOKEN_RE = re.compile(r"[a-z0-9]+")

STOPWORDS = {
    "the", "and", "for", "with", "from", "that", "this", "are", "was", "were",
    "you", "your", "our", "its", "has", "have", "had", "but", "not", "can",
    "will", "would", "should", "could", "into", "out", "off", "over", "under",
    "near", "about", "than", "then", "them", "they", "there", "here", "what",
    "when", "where", "which", "who", "how", "all", "any", "some", "more",
    "most", "very", "also", "just", "one", "two", "day", "days", "trip",
    "place", "places", "visit", "visiting", "want", "need", "please", "give",
    "show", "find", "best", "good", "top", "plan", "planning",
}


def tokenize(text: str) -> list[str]:
    """Lowercase, split on non-alphanumerics, drop stopwords and 1-2 char tokens."""
    if not text:
        return []
    return [
        t
        for t in _TOKEN_RE.findall(str(text).lower())
        if len(t) >= 3 and t not in STOPWORDS
    ]


def norm_key(value) -> str:
    """Normalise a place name for joins/filters: lowercase, alnum only."""
    if value is None:
        return ""
    return re.sub(r"[^a-z0-9]+", "", str(value).lower())


def norm_header(value) -> str:
    """Normalise a CSV header for fuzzy schema resolution."""
    return re.sub(r"[^a-z0-9]+", "", str(value).lower())


def parse_date(value, fallback: date | None = None) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if value:
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y"):
            try:
                return datetime.strptime(str(value).strip(), fmt).date()
            except ValueError:
                continue
    return fallback or date.today()


def date_range(start: date, days: int) -> list[date]:
    return [start + timedelta(days=i) for i in range(max(1, int(days)))]


def strip_markdown(text: str) -> str:
    """Remove markdown emphasis / heading marks for PDF rendering."""
    if not text:
        return ""
    out = re.sub(r"`{1,3}", "", str(text))
    out = re.sub(r"\*{1,3}", "", out)
    out = re.sub(r"^\s{0,3}#{1,6}\s*", "", out, flags=re.MULTILINE)
    out = re.sub(r"^\s{0,3}[-*+]\s+", "- ", out, flags=re.MULTILINE)
    out = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", out)
    return out.strip()


def truncate(text: str, limit: int = 1500) -> str:
    text = str(text)
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + " ... [truncated]"


def money(amount, currency: str = "INR") -> str:
    try:
        return f"{currency} {float(amount):,.0f}"
    except (TypeError, ValueError):
        return f"{currency} -"


def safe_float(value, default=None):
    try:
        if value is None:
            return default
        text = re.sub(r"[^0-9.\-]", "", str(value))
        if text in ("", "-", "."):
            return default
        return float(text)
    except (TypeError, ValueError):
        return default
