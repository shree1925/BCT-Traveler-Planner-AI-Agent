"""Getting CSVs into data/cleaned/ from three sources.

1. Local folder  - files already sitting in data/cleaned/ (the default)
2. Upload        - st.file_uploader
3. URL           - direct CSV link, Google Drive share link, GitHub blob,
                   or Dropbox share link

All three end at the same place: a CSV written into config.DATA_DIR under the
canonical filename for its dataset, so data_layer/loaders.py finds it without
any special casing.
"""

from __future__ import annotations

import io
import re
from pathlib import Path

import pandas as pd
import requests

import config
from data_layer import discovery, schema
from utils.logger import get_logger

log = get_logger(__name__)

MAX_BYTES = 300 * 1024 * 1024  # 300 MB ceiling on downloads
CHUNK = 1 << 16

_DRIVE_ID = re.compile(r"drive\.google\.com/(?:file/d/|open\?id=|uc\?[^/]*id=)([A-Za-z0-9_-]{10,})")
_DRIVE_FOLDER = re.compile(r"drive\.google\.com/drive/folders/")


def normalize_url(url: str) -> tuple[str, str | None]:
    """Share link -> direct-download link.

    Returns (url, warning). Warning is a message to show the user, or None.
    """
    url = (url or "").strip()
    if not url:
        return "", "Enter a URL."

    if _DRIVE_FOLDER.search(url):
        return url, (
            "That is a Google Drive *folder* link. Open the folder, right-click each CSV, "
            "choose 'Get link', and paste the individual file links instead."
        )

    match = _DRIVE_ID.search(url)
    if match:
        return (
            f"https://drive.google.com/uc?export=download&id={match.group(1)}",
            "Make sure the file's sharing is set to 'Anyone with the link'.",
        )

    if "github.com" in url and "/blob/" in url:
        return url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/"), None

    if "dropbox.com" in url:
        stripped = re.sub(r"[?&]dl=[01]", "", url)
        joiner = "&" if "?" in stripped else "?"
        return f"{stripped}{joiner}dl=1", None

    return url, None


def _drive_confirm(session: requests.Session, response: requests.Response, url: str):
    """Drive shows an HTML interstitial for large files. Follow the confirm token."""
    for key, value in session.cookies.items():
        if key.startswith("download_warning"):
            return session.get(url, params={"confirm": value}, stream=True, timeout=60)

    token = re.search(r'name="confirm"\s+value="([^"]+)"', response.text or "")
    if token:
        return session.get(url, params={"confirm": token.group(1)}, stream=True, timeout=60)
    return None


def fetch_to_bytes(url: str) -> tuple[bytes | None, str]:
    """Download a URL into memory. Returns (bytes, message)."""
    direct, warning = normalize_url(url)
    if not direct:
        return None, warning or "Invalid URL."
    if warning and _DRIVE_FOLDER.search(url):
        return None, warning

    try:
        session = requests.Session()
        session.headers["User-Agent"] = config.NOMINATIM_USER_AGENT
        response = session.get(direct, stream=True, timeout=60, allow_redirects=True)

        content_type = (response.headers.get("Content-Type") or "").lower()
        if "text/html" in content_type and "drive.google" in direct:
            retry = _drive_confirm(session, response, direct)
            if retry is not None:
                response = retry
                content_type = (response.headers.get("Content-Type") or "").lower()

        response.raise_for_status()

        if "text/html" in content_type:
            return None, (
                "That link returned a web page, not a file. If it is a Google Drive link, "
                "set sharing to 'Anyone with the link'. Otherwise use a direct CSV URL."
            )

        buffer = io.BytesIO()
        for chunk in response.iter_content(CHUNK):
            buffer.write(chunk)
            if buffer.tell() > MAX_BYTES:
                return None, f"File exceeds the {MAX_BYTES // (1024 * 1024)} MB limit."

        data = buffer.getvalue()
        if not data:
            return None, "The download was empty."
        return data, f"Downloaded {len(data) / 1024:,.0f} KB."

    except requests.Timeout:
        return None, "The download timed out."
    except requests.RequestException as exc:
        return None, f"Download failed: {exc}"


def read_headers(data: bytes) -> tuple[list[str] | None, str]:
    """Parse just enough to confirm it is a usable CSV."""
    # Binary files can slip past pandas as a single junk column - reject early.
    sample = data[:4096]
    if b"\x00" in sample:
        return None, "That looks like a binary file, not a CSV."

    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            frame = pd.read_csv(io.BytesIO(data), nrows=5, encoding=encoding, low_memory=False)
        except UnicodeDecodeError:
            continue
        except Exception as exc:
            return None, f"Not a readable CSV: {str(exc)[:150]}"

        headers = [str(c) for c in frame.columns]
        if len(headers) < 2:
            return None, (
                "Only one column was detected. Check the file is comma-separated "
                "and has a header row."
            )
        unnamed = sum(1 for h in headers if h.lower().startswith("unnamed"))
        if unnamed > len(headers) / 2:
            return None, "Most columns have no header. Check the file has a header row."
        printable = sum(1 for h in headers if h.strip() and h.isprintable())
        if printable < len(headers) / 2:
            return None, "Column headers are not readable text - this may not be a CSV."
        return headers, f"{len(headers)} columns detected."

    return None, "Could not decode the file as CSV (tried utf-8 and latin-1)."


def guess_dataset(filename: str, headers: list[str]) -> tuple[str, float]:
    """Thin wrapper over discovery.score_dataset - single scoring implementation."""
    best, best_score = "", -1.0
    for order, dataset in enumerate(schema.DATASETS):
        score = discovery.score_dataset(dataset, filename, headers) - order * 0.001
        if score > best_score:
            best, best_score = dataset, score
    return best, round(best_score, 2)


def _legacy_guess_dataset(filename: str, headers: list[str]) -> tuple[str, float]:
    """Which of the five datasets does this file look like?

    Scores each dataset by how many of its logical columns resolve against
    these headers, with a bonus for filename overlap.
    """
    best, best_score = "", -1.0
    stem = re.sub(r"[^a-z0-9]+", "", Path(filename).stem.lower())

    for order, (dataset, spec) in enumerate(schema.DATASETS.items()):
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
            score *= 0.3  # heavy penalty: this file cannot drive that dataset

        score -= order * 0.001

        candidates = spec["file"] if isinstance(spec["file"], list) else [spec["file"]]
        for candidate in candidates:
            cand = re.sub(r"[^a-z0-9]+", "", Path(candidate).stem.lower())
            if cand and (cand in stem or stem in cand):
                score += 0.35
                break
        if dataset[:4] in stem:
            score += 0.15

        if score > best_score:
            best, best_score = dataset, score

    return best, round(best_score, 2)


def canonical_name(dataset: str) -> str:
    spec = schema.DATASETS.get(dataset, {})
    candidates = spec.get("file", [f"{dataset}.csv"])
    return candidates[0] if isinstance(candidates, list) else candidates


def save(data: bytes, dataset: str, filename: str | None = None) -> tuple[Path | None, str]:
    """Write bytes into data/cleaned/ keeping the ORIGINAL filename.

    The dataset slot is recorded in the mapping file rather than encoded in
    the filename, so your own names are preserved.
    """
    headers, message = read_headers(data)
    if headers is None:
        return None, message

    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", (filename or f"{dataset}.csv").strip())
    if not safe.lower().endswith(".csv"):
        safe += ".csv"
    path = config.DATA_DIR / safe
    existed = path.exists()

    try:
        path.write_bytes(data)
    except OSError as exc:
        return None, f"Could not write {path.name}: {exc}"

    overrides = discovery.load_overrides()
    overrides = {k: v for k, v in overrides.items() if k != dataset and v != safe}
    overrides[dataset] = safe
    discovery.save_overrides(overrides)

    verb = "Replaced" if existed else "Saved"
    return path, f"{verb} {path.name} -> {dataset} ({len(data) / 1024:,.0f} KB, {len(headers)} columns)."


def clear_cache() -> None:
    """Loaders memoise by path+mtime; clear so the new file is picked up."""
    try:
        import streamlit as st

        st.cache_data.clear()
    except Exception:
        pass


def installed() -> list[dict]:
    """What is currently sitting in data/cleaned/."""
    if not config.DATA_DIR.exists():
        return []
    rows = []
    for path in sorted(config.DATA_DIR.glob("*.csv")):
        try:
            size = path.stat().st_size
        except OSError:
            size = 0
        rows.append({"name": path.name, "kb": size / 1024, "path": path})
    return rows


def remove(name: str) -> str:
    path = config.DATA_DIR / name
    try:
        path.unlink()
        return f"Removed {name}."
    except OSError as exc:
        return f"Could not remove {name}: {exc}"
