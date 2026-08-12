"""Two-stage retrieval over structured CSVs. No embeddings, no vector DB.

Stage 1  hard filter  - deterministic pandas filtering (city, state, type,
                        numeric bands). Does the heavy lifting.
Stage 2  lexical rank - hand-written IDF scoring over the free-text columns
                        of whatever survived stage 1.
Stage 3  serialise    - compact markdown records for the LLM.

Why this instead of embeddings: the data is structured and the schema is
known. Filtering on a city column is exact, instant and free; similarity
search would be slower, fuzzier and would cost an embedding API call per
query.
"""

from __future__ import annotations

import math
from collections import Counter

import pandas as pd

from data_layer import loaders, schema
from utils.helpers import norm_key, safe_float, tokenize, truncate

MAX_SERIALISED_CHARS = 1800


def _build_index(dataset: str, nrows: int) -> tuple[dict, int]:
    del nrows  # cache key only
    df = loaders.load(dataset)
    if df.empty:
        return {}, 0

    text_cols = [
        loaders.col(df, logical)
        for logical in schema.DATASETS[dataset].get("text_columns", [])
    ]
    text_cols = [c for c in text_cols if c]
    if not text_cols:
        return {}, len(df)

    doc_freq: Counter = Counter()
    for _, row in df[text_cols].fillna("").iterrows():
        tokens = set()
        for cell in row:
            tokens.update(tokenize(cell))
        doc_freq.update(tokens)

    return dict(doc_freq), len(df)


_build_index_cached = loaders._cache(_build_index)


def _row_tokens(df: pd.DataFrame, dataset: str) -> pd.Series:
    text_cols = [
        loaders.col(df, logical)
        for logical in schema.DATASETS[dataset].get("text_columns", [])
    ]
    text_cols = [c for c in text_cols if c]
    if not text_cols:
        return pd.Series([[] for _ in range(len(df))], index=df.index)
    joined = df[text_cols].fillna("").astype(str).agg(" ".join, axis=1)
    return joined.map(tokenize)


def lexical_rank(df: pd.DataFrame, dataset: str, query: str, top_k: int) -> pd.DataFrame:
    """IDF-weighted token-overlap ranking, length-normalised."""
    if df.empty:
        return df
    query_tokens = set(tokenize(query))
    if not query_tokens:
        return df.head(top_k)

    doc_freq, total_docs = _build_index_cached(dataset, len(loaders.load(dataset)))
    if not doc_freq or not total_docs:
        return df.head(top_k)

    tokens_per_row = _row_tokens(df, dataset)

    def score(tokens: list[str]) -> float:
        if not tokens:
            return 0.0
        present = query_tokens.intersection(tokens)
        if not present:
            return 0.0
        raw = sum(math.log(total_docs / (1 + doc_freq.get(t, 0))) for t in present)
        return raw / math.sqrt(len(tokens))

    scored = df.copy()
    scored["_score"] = tokens_per_row.map(score)
    scored = scored.sort_values("_score", ascending=False)

    hits = scored[scored["_score"] > 0]
    if len(hits) >= 1:
        return hits.head(top_k)
    return scored.head(top_k)


def filter_rows(
    dataset: str,
    city: str | None = None,
    state: str | None = None,
    place_type: str | None = None,
    min_rating: float | None = None,
    max_price: float | None = None,
    min_price: float | None = None,
) -> pd.DataFrame:
    df = loaders.load(dataset)
    if df.empty:
        return df

    if city:
        key = norm_key(city)
        city_key = loaders.col(df, "city")
        city_key = (city_key + "_key") if city_key and (city_key + "_key") in df.columns else None
        if city_key:
            exact = df[df[city_key] == key]
            if not exact.empty:
                df = exact
            else:
                df = df[df[city_key].str.contains(key, na=False)] if key else df

    if state:
        key = norm_key(state)
        state_col = loaders.col(df, "state")
        state_key = (state_col + "_key") if state_col and (state_col + "_key") in df.columns else None
        if state_key:
            hit = df[df[state_key].str.contains(key, na=False)]
            if not hit.empty:
                df = hit

    if place_type:
        type_col = loaders.col(df, "type")
        if type_col:
            hit = df[df[type_col].astype(str).str.lower().str.contains(place_type.lower(), na=False)]
            if not hit.empty:
                df = hit

    if min_rating is not None:
        rating_col = loaders.col(df, "rating")
        if rating_col:
            numeric = df[rating_col].map(safe_float)
            df = df[numeric.notna() & (numeric >= float(min_rating))]

    price_col = loaders.col(df, "price")
    if price_col and (max_price is not None or min_price is not None):
        numeric = df[price_col].map(safe_float)
        mask = numeric.notna()
        if min_price is not None:
            mask &= numeric >= float(min_price)
        if max_price is not None:
            mask &= numeric <= float(max_price)
        filtered = df[mask]
        if not filtered.empty:
            df = filtered

    return df


def serialise(df: pd.DataFrame, dataset: str, fields: list[str], limit: int) -> str:
    if df.empty:
        return f"No matching records found in the '{dataset}' dataset."

    lines: list[str] = []
    for i, (_, row) in enumerate(df.head(limit).iterrows(), start=1):
        parts: list[str] = []
        for logical in fields:
            column = loaders.col(df, logical)
            if not column:
                continue
            value = row.get(column)
            if value is None or (isinstance(value, float) and pd.isna(value)):
                continue
            text = str(value).strip()
            if not text or text.lower() in ("nan", "none", "-"):
                continue
            if len(text) > 220:
                text = text[:220].rsplit(" ", 1)[0] + "..."
            parts.append(f"{logical}: {text}")
        if parts:
            lines.append(f"{i}. " + " | ".join(parts))

    if not lines:
        return f"No usable records found in the '{dataset}' dataset."

    header = f"Source dataset: {dataset} ({len(df)} matching rows, showing {len(lines)})"
    return truncate(header + "\n" + "\n".join(lines), MAX_SERIALISED_CHARS)


def search(
    dataset: str,
    query: str = "",
    fields: list[str] | None = None,
    top_k: int = 5,
    **filters,
) -> str:
    """Full pipeline: filter -> rank -> serialise. Returns markdown for the LLM."""
    if dataset not in schema.DATASETS:
        return f"Unknown dataset '{dataset}'."

    df = loaders.load(dataset)
    if df.empty:
        path = schema.dataset_path(dataset)
        if path is None:
            return (
                f"The '{dataset}' dataset file is not present in data/cleaned/. "
                f"Tell the user this data is unavailable rather than inventing records."
            )
        return f"The '{dataset}' dataset loaded zero rows from {path.name}."

    filtered = filter_rows(dataset, **filters)
    if filtered.empty:
        return (
            f"No rows in '{dataset}' matched those filters "
            f"({', '.join(f'{k}={v}' for k, v in filters.items() if v is not None) or 'none'}). "
            f"The dataset may not cover that location."
        )

    ranked = lexical_rank(filtered, dataset, query, top_k)
    fields = fields or list(schema.DATASETS[dataset]["columns"])
    return serialise(ranked, dataset, fields, top_k)


def price_bands(city: str | None = None) -> dict:
    """Real accommodation price quantiles from the hotels dataset.

    Returns {} when there is no usable price column - callers must fall back.
    """
    df = filter_rows("hotels", city=city) if city else loaders.load("hotels")
    if df.empty:
        return {}
    price_col = loaders.col(df, "price")
    if not price_col:
        return {}
    numeric = df[price_col].map(safe_float).dropna()
    numeric = numeric[(numeric > 100) & (numeric < 200000)]
    if len(numeric) < 5:
        return {}
    return {
        "Budget": float(numeric.quantile(0.20)),
        "Mid-range": float(numeric.quantile(0.50)),
        "Luxury": float(numeric.quantile(0.85)),
        "sample_size": int(len(numeric)),
        "city": city or "all cities",
    }
