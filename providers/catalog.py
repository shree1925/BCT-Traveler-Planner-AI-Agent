"""Live model catalogs.

Model IDs rotate constantly - Gemini 2.5 Flash was retired for new accounts
mid-project. So instead of hardcoding them, ask each backend what it serves
right now.

    google     -> genai client.models.list(), filtered to Gemini + Gemma
    openrouter -> GET /api/v1/models (public, no key), filtered to Nemotron

Both fall back to config.FALLBACK_MODELS when unreachable, so the picker is
never empty.
"""

from __future__ import annotations

import re

import requests

import config
from utils.logger import get_logger

log = get_logger(__name__)

OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"


def _cache(func):
    try:
        import streamlit as st

        return st.cache_data(show_spinner=False, ttl=3600)(func)
    except Exception:  # pragma: no cover
        store: dict = {}

        def wrapper(*args, **kwargs):
            key = (args, tuple(sorted(kwargs.items())))
            if key not in store:
                store[key] = func(*args, **kwargs)
            return store[key]

        return wrapper


def _sort_google(models: list[str]) -> list[str]:
    """Newest Gemini first, then Gemma, then everything else."""

    def rank(model: str) -> tuple:
        mid = model.lower()
        family = 0 if mid.startswith("gemini") else (1 if mid.startswith("gemma") else 2)
        # Extract the version number so 3.6 sorts above 3.5 above 2.5.
        version = 0.0
        for part in mid.replace("-", " ").split():
            try:
                version = float(part)
                break
            except ValueError:
                continue
        preview = 1 if ("preview" in mid or "exp" in mid) else 0
        return (family, preview, -version, model)

    return sorted(models, key=rank)


def _as_entries(ids: list[str]) -> list[dict]:
    """Plain ids -> the entry shape, deriving vendor from the id prefix.

    Pricing is unknown here, so nothing is claimed as free.
    """
    return [
        {
            "id": i,
            "name": i,
            "vendor": i.split("/")[0] if "/" in i else "google",
            "free": False,
            "context": 0,
            "prompt_cost": 0.0,
            "completion_cost": 0.0,
        }
        for i in ids
    ]


def fetch_google_models(api_key: str) -> tuple[list[dict], str]:
    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        found: list[str] = []
        for model in client.models.list():
            name = (getattr(model, "name", "") or "").replace("models/", "")
            if not name:
                continue
            lowered = name.lower()
            if not (lowered.startswith("gemini") or lowered.startswith("gemma")):
                continue
        
            if any(x in lowered for x in ("embedding", "image", "tts", "veo", "aqa", "imagen")):
                continue
            actions = (
                getattr(model, "supported_actions", None)
                or getattr(model, "supported_generation_methods", None)
                or []
            )
            if actions and not any("generatecontent" in str(a).lower().replace("_", "") for a in actions):
                continue
            found.append(name)

        if not found:
            return _as_entries(config.FALLBACK_MODELS["google"]), "STALE: no chat models returned; press Refresh."
        return _as_entries(_sort_google(found)), f"{len(found)} models available."
    except Exception as exc:
        log.warning("Google model list failed: %s", exc)
        return (
            _as_entries(config.FALLBACK_MODELS["google"]),
            f"STALE offline list — could not reach Google ({str(exc)[:60]}).",
        )


def fetch_openrouter_models(_key: str | None = None) -> tuple[list[dict], str]:
    """Every OpenRouter model that supports tool calling.

    The list is fetched live from OpenRouter's public catalogue (no key
    required), so it is never stale. Models without tool-calling support are
    excluded: this agent cannot function without it, and including them would
    only produce confident invented answers.
    """
    try:
        response = requests.get(OPENROUTER_MODELS_URL, timeout=config.HTTP_TIMEOUT)
        response.raise_for_status()
        payload = response.json() or {}

        found: list[dict] = []
        skipped_no_tools = 0
        for entry in payload.get("data", []):
            model_id = entry.get("id") or ""
            if not model_id:
                continue

            params = [str(p).lower() for p in (entry.get("supported_parameters") or [])]
            if params and "tools" not in params:
                skipped_no_tools += 1
                continue

            pricing = entry.get("pricing") or {}
            try:
                prompt_cost = float(pricing.get("prompt") or 0)
                completion_cost = float(pricing.get("completion") or 0)
            except (TypeError, ValueError):
                prompt_cost = completion_cost = 0.0
            free = model_id.endswith(":free") or (prompt_cost == 0 and completion_cost == 0)

            found.append(
                {
                    "id": model_id,
                    "name": entry.get("name") or model_id,
                    "vendor": model_id.split("/")[0] if "/" in model_id else "",
                    "free": free,
                    "context": entry.get("context_length") or 0,
                    "prompt_cost": prompt_cost,
                    "completion_cost": completion_cost,
                }
            )

        if not found:
            return (
                _as_entries(config.FALLBACK_MODELS["openrouter"]),
                "STALE: no tool-calling models returned; press Refresh.",
            )

        found.sort(key=lambda m: (not m["free"], m["vendor"], -_version_of(m["id"]), m["id"]))
        free_count = sum(1 for m in found if m["free"])
        return found, (
            f"{len(found)} tool-calling models ({free_count} free); "
            f"{skipped_no_tools} without tool support hidden."
        )
    except requests.RequestException as exc:
        log.warning("OpenRouter model list failed: %s", exc)
        return (
            _as_entries(config.FALLBACK_MODELS["openrouter"]),
            f"STALE offline list — could not reach OpenRouter ({str(exc)[:60]}).",
        )


def _list_models(backend: str, api_key: str | None) -> tuple[list[dict], str]:
    if backend == "google":
        if not api_key:
            return _as_entries(config.FALLBACK_MODELS["google"]), "STALE offline list — add a key to load live models."
        return fetch_google_models(api_key)
    if backend == "openrouter":
        return fetch_openrouter_models(api_key)
    return [], f"Unknown backend '{backend}'."


_list_models_cached = _cache(_list_models)


def list_models(backend: str, api_key: str | None = None) -> tuple[list[dict], str]:
    """Returns (entries, note). Each entry has id / name / vendor / free / context."""
    return _list_models_cached(backend, api_key)


def model_ids(entries: list[dict]) -> list[str]:
    return [e["id"] for e in entries]


def _version_of(model_id: str) -> float:
    """Largest version-looking number in a model id.

    Lets 'claude-opus-4.8' sort above 'claude-opus-4.5' and 'deepseek-v4'
    above 'deepseek-v3' without hardcoding version numbers that go stale.
    Parameter and context counts (70b, 235b, 128k, 4m) are ignored - they are
    sizes, not versions.
    """
    best = 0.0
    for match in re.finditer(r"(\d+(?:\.\d+)?)([a-z]*)", model_id.lower()):
        raw, suffix = match.group(1), match.group(2)
        if suffix[:1] in ("b", "k", "m", "t"):  # 70b params, 128k ctx
            continue
        try:
            value = float(raw)
        except ValueError:
            continue
        if value < 100:
            best = max(best, value)
    return best


def vendor_counts(entries: list[dict]) -> dict[str, int]:
    """{vendor: model count}, most models first - drives the vendor picker."""
    counts: dict[str, int] = {}
    for entry in entries:
        vendor = entry.get("vendor") or "other"
        counts[vendor] = counts.get(vendor, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))


def describe(entry: dict) -> str:
    """One-line label for the dropdown."""
    bits = []
    if entry.get("free"):
        bits.append("free")
    ctx = entry.get("context") or 0
    if ctx:
        bits.append(f"{ctx // 1000}k ctx")
    return f"{entry['id']}" + (f"  ({', '.join(bits)})" if bits else "")


def clear_cache() -> None:
    try:
        import streamlit as st

        st.cache_data.clear()
    except Exception:
        pass


def default_model(backend: str, models: list[str]) -> str:  # noqa: D401
    """Preferred default if present, else the first entry."""
    preferred = config.BACKENDS.get(backend, {}).get("default_model")
    if preferred and preferred in models:
        return preferred
    if preferred:
        for model in models:  # tolerate suffixes like -latest / -preview
            if model.startswith(preferred.split(":")[0]):
                return model
    return models[0] if models else (preferred or "")
