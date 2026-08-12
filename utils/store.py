"""Cross-module state.

Tools run inside the Streamlit process, so they write their structured
output here and the UI tabs read it back. Falls back to a plain dict when
imported outside a Streamlit run (unit tests, CLI smoke tests).
"""

from __future__ import annotations

from typing import Any

_FALLBACK: dict[str, Any] = {}


def _backing() -> Any:
    try:
        import streamlit as st

        _ = st.session_state
        return st.session_state
    except Exception:
        return _FALLBACK


def put(key: str, value: Any) -> None:
    _backing()[key] = value


def get(key: str, default: Any = None) -> Any:
    backing = _backing()
    try:
        return backing[key]
    except (KeyError, AttributeError):
        return default


def has(key: str) -> bool:
    return get(key) is not None
