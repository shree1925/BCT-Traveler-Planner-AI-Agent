"""CSV loading + logical-column normalisation.

Each dataset is loaded once, cached by path + mtime, and returned with the
logical column names attached as extra `lc__<logical>` columns. Downstream
code never touches a raw CSV header.
"""

from __future__ import annotations

import pandas as pd

from data_layer import discovery, schema
from utils.helpers import norm_key
from utils.logger import get_logger

log = get_logger(__name__)

LC_PREFIX = "lc__"


def _cache(func):
    """st.cache_data when Streamlit is running, plain memoisation otherwise."""
    try:
        import streamlit as st

        return st.cache_data(show_spinner=False)(func)
    except Exception:  # pragma: no cover
        store: dict = {}

        def wrapper(*args, **kwargs):
            key = (args, tuple(sorted(kwargs.items())))
            if key not in store:
                store[key] = func(*args, **kwargs)
            return store[key]

        return wrapper


def _read_csv(path_str: str, mtime: float) -> pd.DataFrame:
    del mtime  # part of the cache key only
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return pd.read_csv(path_str, encoding=encoding, low_memory=False)
        except UnicodeDecodeError:
            continue
        except Exception as exc:
            log.error("Failed to read %s: %s", path_str, exc)
            return pd.DataFrame()
    return pd.DataFrame()


_read_csv_cached = _cache(_read_csv)


def _prepare(dataset: str, path_str: str, mtime: float) -> pd.DataFrame:
    df = _read_csv_cached(path_str, mtime)
    if df.empty:
        return df

    df = df.copy()
    headers = list(df.columns)
    mapping = schema.resolve_all(dataset, headers)

    for logical, real in mapping.items():
        if real is not None and real in df.columns:
            df[LC_PREFIX + logical] = df[real]

    # Normalised join keys for cheap, case-insensitive filtering.
    for logical in ("city", "state", "name"):
        col = LC_PREFIX + logical
        if col in df.columns:
            df[col + "_key"] = df[col].map(norm_key)

    return df


_prepare_cached = _cache(_prepare)


def load(dataset: str) -> pd.DataFrame:
    """Load one dataset. Returns an empty DataFrame if the file is missing."""
    path = discovery.path_for(dataset)
    if path is None:
        return pd.DataFrame()
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return pd.DataFrame()
    return _prepare_cached(dataset, str(path), mtime)


def col(dataset_df: pd.DataFrame, logical: str) -> str | None:
    """Logical name -> the prepared column, if present."""
    name = LC_PREFIX + logical
    return name if name in dataset_df.columns else None


def health_report() -> list[dict]:
    """One row per dataset for the sidebar Dataset Doctor."""
    report = []
    for dataset, spec in schema.DATASETS.items():
        path = discovery.path_for(dataset)
        df = load(dataset)
        if path is None:
            report.append(
                {
                    "dataset": dataset,
                    "label": spec["label"],
                    "status": "missing",
                    "file": "(no matching file)",
                    "rows": 0,
                    "resolved": {},
                    "unresolved": list(spec["columns"]),
                    "missing_required": list(spec.get("required", [])),
                }
            )
            continue

        mapping = schema.resolve_all(dataset, list(_read_csv_cached(str(path), path.stat().st_mtime).columns))
        resolved = {k: v for k, v in mapping.items() if v}
        unresolved = [k for k, v in mapping.items() if not v]
        missing_required = [r for r in spec.get("required", []) if r in unresolved]

        report.append(
            {
                "dataset": dataset,
                "label": spec["label"],
                "status": "error" if missing_required else ("warn" if unresolved else "ok"),
                "file": path.name,
                "rows": int(len(df)),
                "resolved": resolved,
                "unresolved": unresolved,
                "missing_required": missing_required,
            }
        )
    return report


def loaded_datasets() -> list[str]:
    return [d for d in schema.DATASETS if not load(d).empty]
