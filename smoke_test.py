"""Standalone checks you can run before touching Streamlit.

    python smoke_test.py            # datasets + tools only
    python smoke_test.py --llm      # also round-trips every configured provider
"""

from __future__ import annotations

import sys

import config
from data_layer import loaders


def check_datasets() -> bool:
    print("\n=== DATASETS ===")
    report = loaders.health_report()
    ok = False
    for row in report:
        mark = {"ok": "OK   ", "warn": "WARN ", "error": "ERROR", "missing": "MISS "}[row["status"]]
        print(f"[{mark}] {row['dataset']:<14} {row['file']:<34} rows={row['rows']:>7,}")
        if row["unresolved"]:
            print(f"          unresolved columns: {', '.join(row['unresolved'])}")
        if row["rows"]:
            ok = True
    if not ok:
        print("\n  No dataset loaded. Put your CSVs in data/cleaned/ and check")
        print("  the filenames listed in data_layer/schema.py.")
    return ok


def check_tools() -> None:
    print("\n=== TOOLS ===")
    from tools.currency_tool import convert_currency
    from tools.dataset_tools import search_destinations
    from tools.weather_tool import get_weather_forecast

    print("\n-- convert_currency --")
    print(convert_currency(10000, "INR", "USD"))

    print("\n-- get_weather_forecast --")
    print(get_weather_forecast("Jaipur", days=3))

    print("\n-- search_destinations --")
    print(search_destinations(city="Jaipur", top_k=3))


def check_providers() -> None:
    print("\n=== BACKENDS ===")
    from providers import catalog
    from providers.factory import smoke_test

    for key, meta in config.BACKENDS.items():
        if not config.backend_available(key):
            print(f"[SKIP ] {key:<12} {meta['env']} not set")
            continue

        entries, note = catalog.list_models(key, config.get_secret(meta["env"]))
        print(f"\n  {meta['label']}: {note}")
        for entry in entries[:15]:
            tag = " [free]" if entry.get("free") else ""
            print(f"      {entry['id']}{tag}")
        if len(entries) > 15:
            print(f"      ... and {len(entries) - 15} more")

        model = catalog.default_model(key, catalog.model_ids(entries))
        try:
            print(f"  [OK   ] {model} -> {smoke_test(key, model)[:100]}")
        except Exception as exc:
            print(f"  [FAIL ] {model} -> {str(exc)[:200]}")


if __name__ == "__main__":
    check_datasets()
    check_tools()
    if "--llm" in sys.argv:
        check_providers()
    print("\nDone.")
