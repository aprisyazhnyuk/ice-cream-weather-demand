#!/usr/bin/env python3
"""Download and aggregate Moscow ERA5-Land weather from Open-Meteo."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "weather"
PROCESSED_DIR = ROOT / "data" / "processed"
API_URL = "https://archive-api.open-meteo.com/v1/archive"
PARAMS = {
    "latitude": 55.7558,
    "longitude": 37.6173,
    "start_date": "2021-01-01",
    "end_date": "2025-12-31",
    "daily": ",".join(
        [
            "temperature_2m_mean",
            "temperature_2m_min",
            "temperature_2m_max",
        ]
    ),
    "timezone": "Europe/Moscow",
    "models": "era5_land",
}


def main() -> None:
    response = requests.get(API_URL, params=PARAMS, timeout=90)
    response.raise_for_status()
    payload = response.json()

    daily = payload.get("daily", {})
    dates = daily.get("time", [])
    if not dates:
        raise SystemExit("Open-Meteo response contained no daily observations")

    expected_length = len(dates)
    inconsistent = {
        field: len(values)
        for field, values in daily.items()
        if isinstance(values, list) and len(values) != expected_length
    }
    if inconsistent:
        raise SystemExit(f"Inconsistent daily arrays: {inconsistent}")

    frame = pd.DataFrame(daily)
    frame.insert(0, "market_id", "moscow")
    frame["time"] = pd.to_datetime(frame["time"])
    if frame["time"].duplicated().any():
        raise SystemExit("Duplicate Moscow weather dates returned by source")

    monthly = (
        frame.set_index("time")
        .resample("MS")
        .agg(
            market_id=("market_id", "first"),
            temperature_c=("temperature_2m_mean", "mean"),
            temperature_min_c=("temperature_2m_min", "mean"),
            temperature_max_c=("temperature_2m_max", "mean"),
            observation_days=("market_id", "size"),
        )
        .reset_index(names="period")
    )

    if len(monthly) != 60:
        raise SystemExit(f"Expected 60 complete months, received {len(monthly)}")

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    raw_json_path = RAW_DIR / "moscow_era5_land_2021_2025.json"
    daily_csv_path = RAW_DIR / "moscow_era5_land_daily_2021_2025.csv"
    monthly_csv_path = PROCESSED_DIR / "moscow_weather_monthly_2021_2025.csv"
    metadata_path = RAW_DIR / "moscow_era5_land_2021_2025.metadata.json"

    raw_json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    frame.to_csv(daily_csv_path, index=False, date_format="%Y-%m-%d")
    monthly.to_csv(monthly_csv_path, index=False, date_format="%Y-%m-%d")
    metadata_path.write_text(
        json.dumps(
            {
                "source": API_URL,
                "request_url": response.url,
                "retrieved_at_utc": datetime.now(UTC).isoformat(),
                "model": "era5_land",
                "license": "CC BY 4.0",
                "market_id": "moscow",
                "coordinates": {"latitude": 55.7558, "longitude": 37.6173},
                "daily_rows": len(frame),
                "monthly_rows": len(monthly),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        f"Saved {len(frame)} daily observations and {len(monthly)} monthly rows "
        f"for Moscow ({frame['time'].min().date()} to {frame['time'].max().date()})."
    )


if __name__ == "__main__":
    main()
