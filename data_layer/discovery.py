"""Filename-agnostic dataset discovery.

Drop any CSVs into data/cleaned/ with any names. This module reads their
headers, scores each file against each dataset slot, and assigns the best
overall match. No renaming, no canonical filenames, no restrictions.

A manual override lives in data/cleaned/_mapping.json and always wins, so
you can correct a bad guess from the sidebar.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

import config
from data_layer import schema
from utils.logger import get_logger

log = get_logger(__name__)

MAPPING_FILE = "_mapping.json"
MIN_SCORE = 0.30  


def _cache(func):
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


def _read_headers(path_str: str, mtime: float) -> list[str]:
    del mtime  # cache key only
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            frame = pd.read_csv(path_str, nrows=0, encoding=encoding)
            return [str(c) for c in frame.columns]
        except UnicodeDecodeError:
            continue
        except Exception as exc:
            log.warning("Header read failed for %s: %s", path_str, exc)
            return []
    return []


_read_headers_cached = _cache(_read_headers)


def csv_files() -> list[Path]:
    if not config.DATA_DIR.exists():
        return []
    return sorted(p for p in config.DATA_DIR.glob("*.csv") if not p.name.startswith("_"))


def headers_for(path: Path) -> list[str]:
    try:
        return _read_headers_cached(str(path), path.stat().st_mtime)
    except OSError:
        return []


def score_dataset(dataset: str, filename: str, headers: list[str]) -> float:
    """How strongly does this file look like this dataset slot?"""
    spec = schema.DATASETS.get(dataset)
    if not spec or not headers:
        return 0.0

    logicals = list(spec["columns"])
    
    resolved = sum(1 for lg in logicals if schema.resolve(dataset, lg, headers, strict=True))
    score = resolved / max(1, len(logicals))

    distinctive = {
        "hotels": ["price", "amenities", "star_rating"],
        "itineraries": ["day", "activity"],
        "destinations": ["entry_fee", "time_needed"],
        "cities": ["best_time"],
    }.get(dataset, [])
    if distinctive:
        hits = sum(1 for d in distinctive if schema.resolve(dataset, d, headers, strict=True))
        score += 0.30 * (hits / len(distinctive))

    required = spec.get("required", [])
    if required and not all(schema.resolve(dataset, r, headers, strict=True) for r in required):
        score *= 0.3

    
    stem = re.sub(r"[^a-z0-9]+", "", Path(filename).stem.lower())
    hints = {
        "destinations": ["tourist", "guide", "attraction", "place", "destination", "sight"],
        "hotels": ["hotel", "stay", "accommodation", "goibibo", "property"],
        "itineraries": ["itinerary", "iternary", "plan", "trip", "schedule"],
        "cities": ["city", "cities", "town"],
        "details": ["detail", "detailed"],
    }.get(dataset, [])
    if any(h in stem for h in hints):
        score += 0.35

    return round(score, 3)


def score_matrix() -> dict[str, dict[str, float]]:
    """{filename: {dataset: score}} for every CSV present."""
    matrix: dict[str, dict[str, float]] = {}
    for path in csv_files():
        headers = headers_for(path)
        matrix[path.name] = {ds: score_dataset(ds, path.name, headers) for ds in schema.DATASETS}
    return matrix


def load_overrides() -> dict[str, str]:
    path = config.DATA_DIR / MAPPING_FILE
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {k: v for k, v in data.items() if isinstance(v, str)}
    except Exception as exc:
        log.warning("Could not read mapping file: %s", exc)
        return {}


def save_overrides(mapping: dict[str, str]) -> None:
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = config.DATA_DIR / MAPPING_FILE
    try:
        cleaned = {k: v for k, v in mapping.items() if v}
        path.write_text(json.dumps(cleaned, indent=2), encoding="utf-8")
    except OSError as exc:
        log.warning("Could not write mapping file: %s", exc)


def _assign(matrix_items: tuple, overrides_items: tuple) -> dict[str, str]:
    """Greedy best-match assignment: one file per dataset, one dataset per file."""
    matrix = {f: dict(scores) for f, scores in matrix_items}
    overrides = dict(overrides_items)

    assignment: dict[str, str] = {}
    used_files: set[str] = set()

    
    for dataset, filename in overrides.items():
        if dataset in schema.DATASETS and filename in matrix:
            assignment[dataset] = filename
            used_files.add(filename)

    pairs = [
        (score, filename, dataset)
        for filename, scores in matrix.items()
        for dataset, score in scores.items()
        if score >= MIN_SCORE
    ]
    pairs.sort(reverse=True)

    for score, filename, dataset in pairs:
        if dataset in assignment or filename in used_files:
            continue
        assignment[dataset] = filename
        used_files.add(filename)

    return assignment


_assign_cached = _cache(_assign)


def assignment() -> dict[str, str]:
    matrix = score_matrix()
    matrix_items = tuple((f, tuple(sorted(s.items()))) for f, s in sorted(matrix.items()))
    overrides_items = tuple(sorted(load_overrides().items()))
    return _assign_cached(matrix_items, overrides_items)


def path_for(dataset: str) -> Path | None:
    filename = assignment().get(dataset)
    if not filename:
        return None
    path = config.DATA_DIR / filename
    return path if path.exists() else None


def unassigned_files() -> list[str]:
    assigned = set(assignment().values())
    return [p.name for p in csv_files() if p.name not in assigned]


def clear_cache() -> None:
    try:
        import streamlit as st

        st.cache_data.clear()
    except Exception:
        pass
