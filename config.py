"""Central configuration.

No python-dotenv here - it is not on the allowed dependency list, so `.env`
is parsed by hand (see `_load_dotenv`). Streamlit secrets are used as a
fallback so the app also works on Streamlit Community Cloud.
"""

from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "cleaned"
EXPORT_DIR = BASE_DIR / "exports"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv(BASE_DIR / ".env")


RUNTIME_KEYS = "_runtime_api_keys"


def set_runtime_key(name: str, value: str | None) -> None:
    """Store a key typed into the sidebar for this session only.

    Never written to disk. Takes priority over .env so the user can override
    a stale key without editing files.
    """
    try:
        import streamlit as st

        keys = st.session_state.setdefault(RUNTIME_KEYS, {})
        if value and value.strip():
            keys[name] = value.strip()
        else:
            keys.pop(name, None)
    except Exception:
        pass


def get_secret(name: str) -> str | None:
    """Sidebar entry first, then env var, then Streamlit secrets."""
    try:
        import streamlit as st

        runtime = st.session_state.get(RUNTIME_KEYS, {}).get(name)
        if runtime:
            return runtime
    except Exception:
        pass

    value = os.environ.get(name)
    if value:
        return value.strip()
    try:  
        import streamlit as st

        value = st.secrets.get(name)  
        return str(value).strip() if value else None
    except Exception:
        return None


BACKENDS: dict[str, dict] = {
    "google": {
        "label": "Google AI Studio",
        "sublabel": "Gemini + Gemma",
        "transport": "google",
        "env": "GOOGLE_API_KEY",
        "base_url": None,
        "key_url": "https://aistudio.google.com/apikey",
        "default_model": "gemini-3.6-flash",
    },
    "openrouter": {
        "label": "OpenRouter",
        "sublabel": "Claude, GPT, Gemini, DeepSeek, Nemotron…",
        "transport": "openai",
        "env": "OPENROUTER_API_KEY",
        "base_url": "https://openrouter.ai/api/v1",
        "key_url": "https://openrouter.ai/keys",
        "default_model": "nvidia/nemotron-nano-9b-v2",
    },
}

DEFAULT_BACKEND = "google"

FALLBACK_MODELS: dict[str, list[str]] = {
    "google": [
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-3.1-flash-lite",
        "gemma-4-31b-it",
        "gemma-4-26b-a4b-it",
        "gemma-4-12b-it",
    ],
    
    "openrouter": [
        "nvidia/nemotron-nano-9b-v2",
        "deepseek/deepseek-v4-flash",
        "qwen/qwen3-coder-flash",
    ],
}


def model_supports_temperature(model_id: str) -> bool:
    """Gemini 3.5 and 3.6 removed the sampling parameters entirely.

    Sending temperature to them is an error, so the Google provider omits it.
    """
    mid = (model_id or "").lower()
    return not (mid.startswith("gemini-3.5") or mid.startswith("gemini-3.6"))


def model_extra_body(backend: str, model_id: str) -> dict:
    """Vendor-specific request options merged into the body verbatim."""
    if backend == "openrouter" and "nemotron" in (model_id or "").lower():
        
        
        return {"chat_template_kwargs": {"enable_thinking": False}}
    return {}

TEMPERATURE = 0.4
MAX_OUTPUT_TOKENS = 2048
MAX_AGENT_STEPS = 6
HTTP_TIMEOUT = 15          
LLM_TIMEOUT = 90           
DEFAULT_TOP_K = 5
DEFAULT_CURRENCY = "INR"
NOMINATIM_USER_AGENT = "ai-travel-planner-india/1.0 (student project)"

SUPPORTED_CURRENCIES = ["INR", "USD", "EUR", "GBP", "JPY", "AUD", "CAD", "SGD", "AED"]
BUDGET_STYLES = ["Budget", "Mid-range", "Luxury"]


def backend_available(key: str) -> bool:
    meta = BACKENDS.get(key)
    return bool(meta and get_secret(meta["env"]))


def available_backends() -> list[str]:
    return [k for k in BACKENDS if backend_available(k)]
