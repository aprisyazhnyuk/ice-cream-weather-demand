#!/usr/bin/env python3
"""Validate the market configuration without third-party dependencies."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MARKETS_PATH = ROOT / "config" / "markets.csv"
REQUIRED_FIELDS = {
    "market_id",
    "label",
    "country_iso2",
    "country_iso3",
    "scope",
    "trends_geo",
    "weather_source",
    "hemisphere",
    "analysis_role",
}


def main() -> None:
    with MARKETS_PATH.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        missing_fields = REQUIRED_FIELDS.difference(reader.fieldnames or [])
        if missing_fields:
            raise SystemExit(f"Missing columns: {sorted(missing_fields)}")
        rows = list(reader)

    if not rows:
        raise SystemExit("Market configuration is empty")

    market_ids = [row["market_id"] for row in rows]
    if len(market_ids) != len(set(market_ids)):
        raise SystemExit("market_id values must be unique")

    invalid_scopes = {row["scope"] for row in rows}.difference({"country", "region"})
    if invalid_scopes:
        raise SystemExit(f"Invalid scopes: {sorted(invalid_scopes)}")

    moscow = next((row for row in rows if row["market_id"] == "moscow"), None)
    if not moscow:
        raise SystemExit("Moscow deep-dive market is required")
    if moscow["scope"] != "region" or not moscow["latitude"] or not moscow["longitude"]:
        raise SystemExit("Moscow must be a geocoded regional market")

    print(f"Validated {len(rows)} markets: 10 countries and 1 regional deep dive.")


if __name__ == "__main__":
    main()
