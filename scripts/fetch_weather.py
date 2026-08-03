#!/usr/bin/env python3
"""Download ERA5-Land weather for every configured metropolitan market."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[1]
MARKETS_PATH = ROOT / "config" / "markets.csv"
RAW_DIR = ROOT / "data" / "raw" / "weather"
PROCESSED_DIR = ROOT / "data" / "processed"
API_URL = "https://archive-api.open-meteo.com/v1/archive"
START_DATE = "2021-01-01"
END_DATE = "2025-12-31"
DAILY_FIELDS = [
    "temperature_2m_mean",
    "temperature_2m_min",
    "temperature_2m_max",
]


def load_markets(selected_market: str | None) -> list[dict[str, str]]:
    with MARKETS_PATH.open(newline="", encoding="utf-8") as source:
        markets = list(csv.DictReader(source))
    if selected_market:
        markets = [row for row in markets if row["market_id"] == selected_market]
        if not markets:
            raise SystemExit(f"Unknown market_id: {selected_market}")
    return markets


def fetch_market(
    session: requests.Session, market: dict[str, str]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    params = {
        "latitude": float(market["latitude"]),
        "longitude": float(market["longitude"]),
        "start_date": START_DATE,
        "end_date": END_DATE,
        "daily": ",".join(DAILY_FIELDS),
        "timezone": market["timezone"],
        "models": "era5_land",
    }
    response = session.get(API_URL, params=params, timeout=90)
    response.raise_for_status()
    payload = response.json()
    daily = payload.get("daily", {})
    dates = daily.get("time", [])
    if len(dates) != 1826:
        raise RuntimeError(
            f"{market['market_id']}: expected 1826 days, received {len(dates)}"
        )
    if any(
        len(values) != len(dates)
        for values in daily.values()
        if isinstance(values, list)
    ):
        raise RuntimeError(f"{market['market_id']}: inconsistent daily arrays")

    frame = pd.DataFrame(daily)
    frame.insert(0, "market_id", market["market_id"])
    frame["time"] = pd.to_datetime(frame["time"])
    if frame[DAILY_FIELDS].isna().any().any():
        raise RuntimeError(f"{market['market_id']}: missing temperature observations")

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
        raise RuntimeError(
            f"{market['market_id']}: expected 60 months, received {len(monthly)}"
        )

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    raw_stem = f"{market['market_id']}_era5_land_2021_2025"
    (RAW_DIR / f"{raw_stem}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    frame.to_csv(
        RAW_DIR / f"{market['market_id']}_era5_land_daily_2021_2025.csv",
        index=False,
        date_format="%Y-%m-%d",
    )
    (RAW_DIR / f"{raw_stem}.metadata.json").write_text(
        json.dumps(
            {
                "source": API_URL,
                "request_url": response.url,
                "retrieved_at_utc": datetime.now(UTC).isoformat(),
                "model": "era5_land",
                "license": "CC BY 4.0",
                "market_id": market["market_id"],
                "trends_geo": market["trends_geo"],
                "coordinates": {
                    "latitude": float(market["latitude"]),
                    "longitude": float(market["longitude"]),
                },
                "daily_rows": len(frame),
                "monthly_rows": len(monthly),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return frame, monthly


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--market", help="Fetch one market_id instead of all markets")
    args = parser.parse_args()

    markets = load_markets(args.market)
    monthly_frames: list[pd.DataFrame] = []
    with requests.Session() as session:
        for market in markets:
            _, monthly = fetch_market(session, market)
            monthly_frames.append(monthly)
            print(f"Fetched {market['label']}: 1826 days / 60 months")

    combined = pd.concat(monthly_frames, ignore_index=True)
    if args.market:
        output_path = PROCESSED_DIR / f"{args.market}_weather_monthly_2021_2025.csv"
    else:
        output_path = PROCESSED_DIR / "weather_monthly_2021_2025.csv"
        if len(combined) != len(markets) * 60:
            raise SystemExit("Combined monthly weather row count is invalid")
        if combined.duplicated(["market_id", "period"]).any():
            raise SystemExit("Duplicate market-period weather rows")
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    combined.to_csv(output_path, index=False, date_format="%Y-%m-%d")
    print(f"Saved {len(combined)} monthly rows to {output_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
