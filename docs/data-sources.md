# Data source assessment

## Analytical definition

This project measures **relative search interest** as a proxy for demand intent. It does not claim that a Google Trends index is equivalent to purchases, revenue, or consumption.

## Google Trends

- Variable: interest over time for the **Ice cream** topic, rather than an English-language search term.
- Window: 2021-01-01 through 2025-12-31.
- Raw resolution: weekly where available.
- Analytical resolution: monthly.
- Geography: one independently exported series per country; Moscow uses `RU-MOW` if Google Trends returns sufficient observations.
- Acquisition: official CSV export from Google Trends Explore. The official API is currently restricted to approved alpha testers.
- Attribution: `Data source: Google Trends` with a link to Google Trends.

### Comparability constraint

Public Google Trends exports are sampled and normalized to 0–100 within the requested geography and period. An index of 80 in one independently exported country is not evidence of the same absolute search volume as 80 in another country.

Valid comparisons include:

- response shape within each market;
- correlation or fitted temperature sensitivity within each market;
- standardized anomalies;
- the temperature at which each fitted curve reaches a defined share of its own range.

Invalid claims include absolute rankings of search demand across independently normalized country exports.

## Country weather

- Source: World Bank Climate Change Knowledge Portal (CCKP).
- Underlying dataset: ERA5 0.25-degree reanalysis from ECMWF.
- Variable: mean surface-air temperature (`tas`).
- Resolution: monthly, spatially aggregated to national boundaries.
- License: World Bank-produced datasets default to CC BY 4.0; exact downloaded artifact metadata must be retained.

Country aggregation is preferred to capital-city weather because the corresponding search-interest series is national.

## Moscow weather

- Source interface: Open-Meteo Historical Weather API.
- Underlying data: ERA5/ERA5-Land reanalysis.
- Point: 55.7558 N, 37.6173 E.
- Variables: daily mean, minimum, and maximum 2 m temperature. ERA5-Land did not provide valid apparent-temperature or precipitation values for the tested request, so those fields are deliberately excluded.
- License: CC BY 4.0 for the Historical Weather API.

Moscow is treated as a separate regional case study rather than mixed into national rankings without a scope indicator.

## Proposed analytical fields

| Field | Meaning |
|---|---|
| `period` | Month start date |
| `market_id` | Stable project market key |
| `scope` | `country` or `region` |
| `interest_index` | Google Trends value after monthly aggregation |
| `temperature_c` | Mean 2 m/surface-air temperature in Celsius |
| `interest_zscore` | Within-market standardized interest |
| `temperature_anomaly_c` | Temperature minus market/month climatology |
| `interest_anomaly` | Interest minus market/month seasonal baseline |
| `scoop_point_c` | Model-derived half-rise temperature |

## Quality controls

1. Preserve raw downloads unchanged and record retrieval dates.
2. Reject duplicate market-period rows.
3. Track partial Google Trends observations explicitly.
4. Do not interpolate missing interest silently.
5. Fit country models independently.
6. Separate seasonal association from anomaly-based weather response.
7. Report sample size and uncertainty with every model result.
8. Call out lower Google market share as a limitation where relevant, particularly for Russia.

## Sources

- Google Trends FAQ: https://support.google.com/trends/answer/4365533
- Google Trends export and citation guidance: https://support.google.com/trends/answer/4365538
- Google Trends API alpha: https://developers.google.com/search/apis/trends
- World Bank CCKP downloads and API: https://climateknowledgeportal.worldbank.org/download-data
- World Bank CCKP metadata: https://climateknowledgeportal.worldbank.org/metadata
- Open-Meteo Historical Weather API: https://open-meteo.com/en/docs/historical-weather-api
