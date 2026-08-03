#!/usr/bin/env python3
"""Validate official Google Trends CSV exports and combine them monthly."""

from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MARKETS_PATH = ROOT / "config" / "markets.csv"
RAW_DIR = ROOT / "data" / "raw" / "google_trends"
OUTPUT_PATH = ROOT / "data" / "processed" / "trends_monthly_2021_2025.csv"
PERIOD_NAMES = {"day", "week", "month"}


def load_market_ids() -> list[str]:
    with MARKETS_PATH.open(newline="", encoding="utf-8") as source:
        return [row["market_id"] for row in csv.DictReader(source)]


def find_header_row(path: Path) -> int:
    with path.open(encoding="utf-8-sig") as source:
        for index, line in enumerate(source):
            first_cell = line.split(",", 1)[0].strip().lower()
            if first_cell in PERIOD_NAMES:
                return index
    raise ValueError(f"{path.name}: could not locate Day/Week/Month header")


def parse_interest(value: object) -> tuple[float, bool]:
    text = str(value).strip()
    if text == "<1":
        return 0.5, True
    return float(text), False


def load_export(market_id: str) -> pd.DataFrame:
    path = RAW_DIR / f"{market_id}.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path.relative_to(ROOT)}; follow docs/google-trends-export.md"
        )
    header_row = find_header_row(path)
    frame = pd.read_csv(path, skiprows=header_row, encoding="utf-8-sig")
    if len(frame.columns) != 2:
        raise ValueError(f"{path.name}: expected two columns, found {len(frame.columns)}")

    period_column, interest_column = frame.columns
    source_resolution = str(period_column).lower()
    frame = frame.rename(columns={period_column: "period", interest_column: "raw_interest"})
    frame["period"] = pd.to_datetime(frame["period"], errors="raise")
    parsed = frame["raw_interest"].map(parse_interest)
    frame["interest_index"] = parsed.map(lambda pair: pair[0])
    frame["is_below_one"] = parsed.map(lambda pair: pair[1])
    frame["market_id"] = market_id

    if source_resolution == "week":
        expanded_rows: list[dict[str, object]] = []
        for row in frame.itertuples(index=False):
            for day in pd.date_range(row.period, periods=7, freq="D"):
                if pd.Timestamp("2021-01-01") <= day <= pd.Timestamp("2025-12-31"):
                    expanded_rows.append(
                        {
                            "period": day,
                            "interest_index": row.interest_index,
                            "is_below_one": row.is_below_one,
                        }
                    )
        frame = pd.DataFrame(expanded_rows)

    frame["period"] = frame["period"].dt.to_period("M").dt.to_timestamp()
    monthly = (
        frame.groupby("period", as_index=False)
        .agg(
            interest_index=("interest_index", "mean"),
            below_one_share=("is_below_one", "mean"),
        )
        .assign(market_id=market_id, source_resolution=source_resolution)
    )
    if len(monthly) != 60:
        raise ValueError(f"{path.name}: expected 60 months, produced {len(monthly)}")
    return monthly[
        [
            "period",
            "market_id",
            "interest_index",
            "below_one_share",
            "source_resolution",
        ]
    ]


def main() -> None:
    market_ids = load_market_ids()
    combined = pd.concat([load_export(market_id) for market_id in market_ids])
    if combined.duplicated(["market_id", "period"]).any():
        raise SystemExit("Duplicate market-period Trends rows")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(OUTPUT_PATH, index=False, date_format="%Y-%m-%d")
    print(f"Imported {len(combined)} rows from {len(market_ids)} Trends exports")


if __name__ == "__main__":
    main()
