"""Sidebar: provider picker, trip parameters, dataset health."""

from __future__ import annotations

import os
from datetime import date, timedelta

import streamlit as st

import config
from data_layer import loaders
from ui import data_panel
from providers import catalog
from providers.factory import smoke_test
from ui.components import chip


KEY_FIELDS = [
    (meta["env"], meta["label"], meta["sublabel"], meta["key_url"])
    for meta in config.BACKENDS.values()
]


def _api_keys() -> None:
    configured = sum(1 for env, *_ in KEY_FIELDS if config.get_secret(env))
    with st.expander(f"API keys ({configured}/{len(KEY_FIELDS)} set)", expanded=configured == 0):
        st.caption(
            "Paste a key to use it for this session only - nothing is written to disk. "
            "Keys already in your `.env` are picked up automatically."
        )
        for env, vendor, unlocks, url in KEY_FIELDS:
            from_env = bool(os.environ.get(env))
            entered = st.text_input(
                f"{vendor} — {unlocks}",
                value="",
                type="password",
                key=f"input_{env}",
                placeholder="loaded from .env" if from_env else f"paste your {env}",
                help=f"Free key: {url}",
            )
            config.set_runtime_key(env, entered)

            if config.get_secret(env):
                source = "typed here" if entered.strip() else ".env"
                st.markdown(chip(f"active ({source})", "ok"), unsafe_allow_html=True)
            else:
                st.markdown(f"[Get a free key]({url})")

        if st.button("Clear typed keys", use_container_width=True):
            st.session_state[config.RUNTIME_KEYS] = {}
            for env, *_ in KEY_FIELDS:
                st.session_state.pop(f"input_{env}", None)
            st.rerun()


def _model_picker() -> tuple[str, str]:
    st.markdown("### Model")

    keys = list(config.BACKENDS)
    labels = {
        k: f"{'🟢' if config.backend_available(k) else '🔴'} {config.BACKENDS[k]['label']}"
           f" — {config.BACKENDS[k]['sublabel']}"
        for k in keys
    }
    stored = st.session_state.get("backend_choice", config.DEFAULT_BACKEND)
    backend = st.selectbox(
        "Backend",
        keys,
        index=keys.index(stored) if stored in keys else 0,
        format_func=lambda k: labels[k],
        label_visibility="collapsed",
    )
    st.session_state["backend_choice"] = backend
    meta = config.BACKENDS[backend]

    if not config.backend_available(backend):
        st.warning(f"No `{meta['env']}` yet — add it in the API keys panel above.")
        return backend, meta["default_model"]

    entries, note = catalog.list_models(backend, config.get_secret(meta["env"]))
    if not entries:
        st.error(note)
        return backend, meta["default_model"]

    if backend == "openrouter":
        vendors = catalog.vendor_counts(entries)
        picked = st.multiselect(
            "Vendors",
            options=list(vendors),
            default=st.session_state.get("or_vendors", []),
            format_func=lambda v: f"{v} ({vendors[v]})",
            key="or_vendors",
            placeholder="All vendors",
        )

        col_a, col_b = st.columns([3, 2])
        query = col_a.text_input(
            "Filter", value=st.session_state.get("or_query", ""),
            key="or_query", placeholder="search model name",
            label_visibility="collapsed",
        )
        free_only = col_b.checkbox("Free only", value=st.session_state.get("or_free", False),
                                   key="or_free")

        filtered = [
            e for e in entries
            if (not picked or e["vendor"] in picked)
            and (not query.strip() or query.strip().lower() in e["id"].lower())
            and (not free_only or e["free"])
        ]
        if not filtered:
            st.warning(f"Nothing matches those filters. Showing all {len(entries)}.")
            filtered = entries
        st.caption(f"{len(filtered)} of {len(entries)} shown")
        entries = filtered

    ids = catalog.model_ids(entries)
    lookup = {e["id"]: e for e in entries}

    state_key = f"model_choice_{backend}"
    current = st.session_state.get(state_key) or catalog.default_model(backend, ids)
    model = st.selectbox(
        "Model",
        ids,
        index=ids.index(current) if current in ids else 0,
        format_func=lambda i: catalog.describe(lookup[i]),
        key=f"select_{state_key}",
    )
    st.session_state[state_key] = model
    if note.startswith("STALE"):
        st.warning(note.replace("STALE", "").lstrip(": —").strip().capitalize()
                   + " — this list may be out of date.")
    else:
        st.caption(note)

    col1, col2 = st.columns(2)
    if col1.button("Refresh list", use_container_width=True):
        catalog.clear_cache()
        st.rerun()
    if col2.button("Test", use_container_width=True):
        with st.spinner("Saying hello..."):
            try:
                st.success(smoke_test(backend, model)[:300])
            except Exception as exc:
                st.error(str(exc)[:400])

    return backend, model


def _trip_form() -> dict:
    st.markdown("### Trip")
    destination = st.text_input("Destination city", value=st.session_state.get("dest", "Jaipur"))
    st.session_state["dest"] = destination

    today = date.today()
    col1, col2 = st.columns(2)
    start = col1.date_input("Start", value=today + timedelta(days=7), min_value=today)
    end = col2.date_input("End", value=today + timedelta(days=10), min_value=start)

    travellers = st.number_input("Travellers", min_value=1, max_value=20, value=2, step=1)
    style = st.radio("Style", config.BUDGET_STYLES, index=1, horizontal=True)
    currency = st.selectbox("Show costs also in", config.SUPPORTED_CURRENCIES, index=1)

    days = max(1, (end - start).days + 1)
    st.caption(f"{days} day trip")

    planned = st.button("Plan my trip", type="primary", use_container_width=True)

    return {
        "destination": destination,
        "start": start,
        "days": days,
        "travellers": int(travellers),
        "style": style,
        "currency": currency,
        "submitted": planned,
    }


def _dataset_doctor() -> None:
    st.markdown("### Datasets")
    data_panel.render()

    report = loaders.health_report()

    total_rows = sum(r["rows"] for r in report)
    ok_count = sum(1 for r in report if r["status"] == "ok")
    st.caption(f"{ok_count}/{len(report)} clean · {total_rows:,} rows loaded")

    for row in report:
        icon = {"ok": "🟢", "warn": "🟡", "error": "🔴", "missing": "⚪"}[row["status"]]
        st.markdown(f"{icon} **{row['label']}** — {row['rows']:,} rows")

    with st.expander("Dataset Doctor", expanded=False):
        st.caption(
            "Column names resolved from `data_layer/schema.py`. Anything unresolved is a "
            "column this app could not find in your CSV — fix the mapping there."
        )
        for row in report:
            st.markdown(f"**{row['dataset']}** · `{row['file']}`")
            if row["status"] == "missing":
                st.markdown(chip("file not found in data/cleaned/", "warn"), unsafe_allow_html=True)
                st.divider()
                continue
            if row["missing_required"]:
                st.markdown(
                    chip("missing required: " + ", ".join(row["missing_required"]), "warn"),
                    unsafe_allow_html=True,
                )
            if row["resolved"]:
                st.json({k: v for k, v in row["resolved"].items()}, expanded=False)
            if row["unresolved"]:
                st.caption("Unresolved: " + ", ".join(row["unresolved"]))
            st.divider()

        if st.button("Reload datasets", use_container_width=True):
            st.cache_data.clear()
            st.rerun()


def render() -> dict:
    with st.sidebar:
        st.markdown("## ✈️ Controls")
        _api_keys()
        st.divider()
        backend, model = _model_picker()
        st.divider()
        trip = _trip_form()
        st.divider()
        _dataset_doctor()
        st.divider()
        if st.button("Clear conversation", use_container_width=True):
            st.session_state["messages"] = []
            st.session_state["history"] = []
            st.rerun()

    trip["backend"] = backend
    trip["model"] = model
    return trip
