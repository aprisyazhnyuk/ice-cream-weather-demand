#!/usr/bin/env python3
"""Join source series and calculate market-level analytical features."""

from __future__ import annotations

import csv
import json
from calendar import month_abbr
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import linregress, pearsonr


ROOT = Path(__file__).resolve().parents[1]
MARKETS_PATH = ROOT / "config" / "markets.csv"
WEATHER_PATH = ROOT / "data" / "processed" / "weather_monthly_2021_2025.csv"
TRENDS_PATH = ROOT / "data" / "processed" / "trends_monthly_2021_2025.csv"
ANALYSIS_PATH = ROOT / "data" / "processed" / "analysis_monthly_2021_2025.csv"
SUMMARY_PATH = ROOT / "data" / "processed" / "market_summary.csv"
WEB_PATH = ROOT / "data" / "processed" / "chart_data.json"


def isotonic_increasing(values: np.ndarray) -> np.ndarray:
    """Return an equal-weight increasing PAVA fit."""
    blocks: list[list[float | int]] = []
    for index, value in enumerate(values):
        blocks.append([index, index, float(value), 1])
        while len(blocks) > 1 and blocks[-2][2] > blocks[-1][2]:
            right = blocks.pop()
            left = blocks.pop()
            weight = int(left[3]) + int(right[3])
            level = (
                float(left[2]) * int(left[3])
                + float(right[2]) * int(right[3])
            ) / weight
            blocks.append([int(left[0]), int(right[1]), level, weight])

    fitted = np.empty(len(values), dtype=float)
    for start, end, level, _ in blocks:
        fitted[int(start) : int(end) + 1] = float(level)
    return fitted


def activation_temperature(climatology: pd.DataFrame) -> float:
    """Temperature where monotonic seasonal interest reaches half its fitted rise."""
    ordered = climatology.sort_values("temperature_c")
    temperatures = ordered["temperature_c"].to_numpy(dtype=float)
    fitted = isotonic_increasing(ordered["interest_index"].to_numpy(dtype=float))
    target = fitted.min() + 0.5 * (fitted.max() - fitted.min())
    crossing = int(np.argmax(fitted >= target))
    if crossing == 0 or fitted[crossing] == fitted[crossing - 1]:
        return float(temperatures[crossing])
    share = (target - fitted[crossing - 1]) / (
        fitted[crossing] - fitted[crossing - 1]
    )
    return float(
        temperatures[crossing - 1]
        + share * (temperatures[crossing] - temperatures[crossing - 1])
    )


def strength_label(correlation: float) -> str:
    absolute = abs(correlation)
    if absolute >= 0.5:
        return "strong"
    if absolute >= 0.3:
        return "moderate"
    return "weak"


def main() -> None:
    with MARKETS_PATH.open(newline="", encoding="utf-8") as source:
        markets = pd.DataFrame(csv.DictReader(source))

    weather = pd.read_csv(WEATHER_PATH, parse_dates=["period"])
    trends = pd.read_csv(TRENDS_PATH, parse_dates=["period"])
    analysis = weather.merge(
        trends, on=["market_id", "period"], how="inner", validate="one_to_one"
    ).merge(markets, on="market_id", how="left", validate="many_to_one")

    if len(analysis) != 600:
        raise SystemExit(f"Expected 600 joined rows, received {len(analysis)}")
    if analysis.isna().any().any():
        missing = analysis.columns[analysis.isna().any()].tolist()
        raise SystemExit(f"Joined analysis contains missing values: {missing}")
    if analysis.duplicated(["market_id", "period"]).any():
        raise SystemExit("Joined analysis contains duplicate market-period rows")

    analysis["year"] = analysis["period"].dt.year
    analysis["month"] = analysis["period"].dt.month
    analysis["month_name"] = analysis["month"].map(lambda value: month_abbr[value])
    analysis["interest_zscore"] = analysis.groupby("market_id")[
        "interest_index"
    ].transform(lambda values: (values - values.mean()) / values.std(ddof=0))
    analysis["interest_scaled"] = analysis.groupby("market_id")[
        "interest_index"
    ].transform(
        lambda values: (values - values.min()) / (values.max() - values.min())
    )
    analysis["temperature_climatology_c"] = analysis.groupby(
        ["market_id", "month"]
    )["temperature_c"].transform("mean")
    analysis["interest_climatology"] = analysis.groupby(["market_id", "month"])[
        "interest_index"
    ].transform("mean")
    analysis["temperature_anomaly_c"] = (
        analysis["temperature_c"] - analysis["temperature_climatology_c"]
    )
    analysis["interest_anomaly"] = (
        analysis["interest_index"] - analysis["interest_climatology"]
    )

    summaries: list[dict[str, object]] = []
    for market_id, group in analysis.groupby("market_id", sort=False):
        seasonal = pearsonr(group["temperature_c"], group["interest_index"])
        anomaly = pearsonr(
            group["temperature_anomaly_c"], group["interest_anomaly"]
        )
        seasonal_fit = linregress(group["temperature_c"], group["interest_index"])
        anomaly_fit = linregress(
            group["temperature_anomaly_c"], group["interest_anomaly"]
        )
        climatology = (
            group.groupby("month", as_index=False)
            .agg(
                temperature_c=("temperature_c", "mean"),
                interest_index=("interest_index", "mean"),
            )
            .sort_values("month")
        )
        peak = climatology.loc[climatology["interest_index"].idxmax()]
        market = group.iloc[0]
        summaries.append(
            {
                "market_id": market_id,
                "label": market["label"],
                "country_iso2": market["country_iso2"],
                "trends_geo": market["trends_geo"],
                "hemisphere": market["hemisphere"],
                "analysis_role": market["analysis_role"],
                "seasonal_correlation": seasonal.statistic,
                "seasonal_p_value": seasonal.pvalue,
                "seasonal_slope_per_c": seasonal_fit.slope,
                "anomaly_correlation": anomaly.statistic,
                "anomaly_p_value": anomaly.pvalue,
                "anomaly_slope_per_c": anomaly_fit.slope,
                "anomaly_response_strength": strength_label(anomaly.statistic),
                "scoop_point_c": activation_temperature(climatology),
                "peak_interest_month": month_abbr[int(peak["month"])],
                "peak_interest_index": peak["interest_index"],
                "peak_temperature_c": peak["temperature_c"],
                "minimum_temperature_c": group["temperature_c"].min(),
                "maximum_temperature_c": group["temperature_c"].max(),
                "temperature_span_c": (
                    group["temperature_c"].max() - group["temperature_c"].min()
                ),
            }
        )

    summary = pd.DataFrame(summaries).sort_values("scoop_point_c")
    numeric_columns = summary.select_dtypes(include="number").columns
    summary[numeric_columns] = summary[numeric_columns].round(4)
    analysis = analysis.sort_values(["market_id", "period"])
    analysis.to_csv(ANALYSIS_PATH, index=False, date_format="%Y-%m-%d")
    summary.to_csv(SUMMARY_PATH, index=False)

    web_series = analysis[
        [
            "period",
            "market_id",
            "temperature_c",
            "interest_index",
            "interest_scaled",
            "temperature_anomaly_c",
            "interest_anomaly",
        ]
    ].copy()
    web_series["period"] = web_series["period"].dt.strftime("%Y-%m-%d")
    web_series = web_series.round(4)
    WEB_PATH.write_text(
        json.dumps(
            {
                "metadata": {
                    "period_start": "2021-01-01",
                    "period_end": "2025-12-31",
                    "market_count": 10,
                    "monthly_observation_count": 600,
                    "demand_proxy": "Google Trends relative search interest",
                    "weather_source": "Open-Meteo ERA5-Land",
                    "scoop_point_definition": (
                        "Temperature where the monotonic monthly climatology reaches "
                        "half of its fitted interest rise"
                    ),
                },
                "markets": summary.to_dict(orient="records"),
                "series": web_series.to_dict(orient="records"),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(
        f"Built {len(analysis)} analytical rows, {len(summary)} market summaries, "
        "and chart_data.json"
    )


if __name__ == "__main__":
    main()
