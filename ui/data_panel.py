"""Data source panel: local folder / upload / URL.

Rendered inside the sidebar's Datasets section.
"""

from __future__ import annotations

import streamlit as st

import config
from data_layer import discovery, schema, sources
from ui.components import chip

DATASET_LABELS = {key: spec["label"] for key, spec in schema.DATASETS.items()}


def _dataset_selector(default: str, key: str, score: float | None = None) -> str:
    options = list(schema.DATASETS)
    index = options.index(default) if default in options else 0
    label = "Which dataset is this?"
    if score is not None:
        confidence = "high" if score >= 0.6 else "low"
        label += f"  (auto-detected, {confidence} confidence)"
    return st.selectbox(
        label,
        options,
        index=index,
        format_func=lambda k: DATASET_LABELS[k],
        key=key,
    )


def _upload_tab() -> None:
    st.caption(
        "Drop your cleaned CSVs here. Each file is auto-matched to a dataset by its "
        "column names — confirm or change the match, then save."
    )
    uploads = st.file_uploader(
        "CSV files",
        type=["csv"],
        accept_multiple_files=True,
        key="dataset_uploader",
        label_visibility="collapsed",
    )
    if not uploads:
        return

    for index, upload in enumerate(uploads):
        data = upload.getvalue()
        headers, message = sources.read_headers(data)

        st.markdown(f"**{upload.name}** · {len(data) / 1024:,.0f} KB")
        if headers is None:
            st.markdown(chip(message, "warn"), unsafe_allow_html=True)
            st.divider()
            continue

        guess, score = sources.guess_dataset(upload.name, headers)
        target = _dataset_selector(guess, key=f"up_target_{index}", score=score)

        resolved = schema.resolve_all(target, headers)
        matched = sum(1 for v in resolved.values() if v)
        st.markdown(
            chip(f"{matched}/{len(resolved)} columns matched", "ok" if matched >= 3 else "warn"),
            unsafe_allow_html=True,
        )
        missing = [k for k, v in resolved.items() if not v]
        if missing:
            st.caption("Unmatched: " + ", ".join(missing))

        if st.button(f"Save to '{target}' slot", key=f"up_save_{index}",
                     use_container_width=True):
            path, result = sources.save(data, target, filename=upload.name)
            if path:
                sources.clear_cache()
                st.success(result)
                st.rerun()
            else:
                st.error(result)
        st.divider()


def _url_tab() -> None:
    st.caption(
        "Paste a direct CSV link, a Google Drive share link, or a GitHub file URL. "
        "Drive files must be shared as 'Anyone with the link'."
    )
    url = st.text_input("URL", key="dataset_url", placeholder="https://drive.google.com/file/d/...")

    if st.button("Fetch", use_container_width=True, key="fetch_url"):
        if not url.strip():
            st.warning("Enter a URL first.")
        else:
            with st.spinner("Downloading..."):
                data, message = sources.fetch_to_bytes(url)
            if data is None:
                st.error(message)
            else:
                st.session_state["fetched_bytes"] = data
                st.session_state["fetched_name"] = url.rsplit("/", 1)[-1][:60] or "download.csv"
                st.success(message)

    data = st.session_state.get("fetched_bytes")
    if not data:
        return

    headers, message = sources.read_headers(data)
    if headers is None:
        st.error(message)
        return

    name = st.session_state.get("fetched_name", "download.csv")
    guess, score = sources.guess_dataset(name, headers)
    target = _dataset_selector(guess, key="url_target", score=score)

    resolved = schema.resolve_all(target, headers)
    matched = sum(1 for v in resolved.values() if v)
    st.markdown(
        chip(f"{matched}/{len(resolved)} columns matched", "ok" if matched >= 3 else "warn"),
        unsafe_allow_html=True,
    )

    if st.button(f"Save to '{target}' slot", use_container_width=True, key="url_save"):
        path, result = sources.save(data, target, filename=name)
        if path:
            sources.clear_cache()
            st.session_state.pop("fetched_bytes", None)
            st.success(result)
            st.rerun()
        else:
            st.error(result)


def _mapping_tab() -> None:
    files = [p.name for p in discovery.csv_files()]
    if not files:
        st.caption("No CSVs in the folder yet.")
        return

    st.caption(
        "Any filenames work — files are matched to slots by their column headers. "
        "Override anything that landed in the wrong slot."
    )

    current = discovery.assignment()
    overrides = discovery.load_overrides()
    matrix = discovery.score_matrix()
    changed = {}

    for dataset, spec in schema.DATASETS.items():
        options = ["(auto)"] + files
        assigned = current.get(dataset)
        pinned = overrides.get(dataset)
        index = options.index(pinned) if pinned in options else 0

        pick = st.selectbox(
            spec["label"],
            options,
            index=index,
            key=f"map_{dataset}",
            help=f"Slot: {dataset}",
        )
        changed[dataset] = "" if pick == "(auto)" else pick

        if assigned:
            score = matrix.get(assigned, {}).get(dataset, 0)
            kind = "ok" if score >= 0.6 else "warn"
            source = "pinned" if pinned else f"auto, score {score:.2f}"
            st.markdown(chip(f"{assigned} ({source})", kind), unsafe_allow_html=True)
        else:
            st.markdown(chip("no file matched", "warn"), unsafe_allow_html=True)

    spare = discovery.unassigned_files()
    if spare:
        st.caption("Not used by any slot: " + ", ".join(spare))

    col1, col2 = st.columns(2)
    if col1.button("Save mapping", use_container_width=True, type="primary"):
        discovery.save_overrides({k: v for k, v in changed.items() if v})
        discovery.clear_cache()
        sources.clear_cache()
        st.rerun()
    if col2.button("Reset to auto", use_container_width=True):
        discovery.save_overrides({})
        discovery.clear_cache()
        sources.clear_cache()
        st.rerun()


def _folder_tab() -> None:
    st.caption(f"Files currently in `{config.DATA_DIR.as_posix()}`")
    rows = sources.installed()
    if not rows:
        st.markdown(chip("empty", "warn"), unsafe_allow_html=True)
        st.caption("Copy the samples to try it immediately:")
        st.code("cp data/sample/*.csv data/cleaned/", language="bash")
        return

    for row in rows:
        left, right = st.columns([4, 1])
        left.markdown(f"`{row['name']}` · {row['kb']:,.0f} KB")
        if right.button("✕", key=f"rm_{row['name']}", help=f"Remove {row['name']}"):
            message = sources.remove(row["name"])
            sources.clear_cache()
            st.toast(message)
            st.rerun()

    if st.button("Reload from disk", use_container_width=True, key="reload_disk"):
        sources.clear_cache()
        st.rerun()


def render() -> None:
    with st.expander("Add or replace datasets", expanded=not sources.installed()):
        mapping, folder, upload, url = st.tabs(
            ["🔗 Mapping", "📁 Folder", "⬆️ Upload", "🔗 URL / Drive"]
        )
        with mapping:
            _mapping_tab()
        with folder:
            _folder_tab()
        with upload:
            _upload_tab()
        with url:
            _url_tab()
