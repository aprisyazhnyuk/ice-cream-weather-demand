# Analysis methodology

## Unit of analysis

The analytical table contains one row per market and calendar month from January 2021 through December 2025: 10 markets × 60 months = 600 observations.

Weekly Google Trends values are expanded across their seven represented days before monthly averaging. This prevents a week crossing a month boundary from being assigned wholly to its start month. ERA5-Land daily temperature is averaged directly to calendar month.

## Two different temperature relationships

### Seasonal association

Pearson correlation between monthly temperature and monthly search interest measures whether warm parts of the year tend to coincide with stronger ice-cream interest. Both variables contain a repeating seasonal cycle, so this is descriptive rather than causal.

### Weather-anomaly response

For every market and calendar month, the five-year January, February, and other month-specific means are calculated. These baselines are subtracted from each observation before correlation:

```text
temperature anomaly = observed temperature − market/month mean temperature
interest anomaly    = observed interest − market/month mean interest
```

The resulting correlation asks a narrower question: when a month is warmer than that market's usual version of the same calendar month, is ice-cream interest also unusually high? This removes the normal seasonal cycle, but it still does not prove causation.

## Scoop point

The **scoop point** is a descriptive threshold built from each market's 12 monthly climatology points:

1. Average temperature and interest for each calendar month across 2021–2025.
2. Sort the 12 points from coldest to warmest.
3. Fit an increasing isotonic curve using the pool-adjacent-violators algorithm.
4. Find the temperature at which that fitted curve reaches halfway between its minimum and maximum interest.

This makes the threshold robust to small reversals in monthly interest while avoiding an unsupported claim about sales volumes. It is comparable as a response temperature, not as an absolute demand level.

## Interpretation limits

- Google Trends values are independently normalized within each geography.
- Search interest is a demand-intent proxy, not sales.
- City-centre ERA5-Land temperatures approximate conditions in broader Trends subregions.
- London uses England search interest because Greater London is not supported for this query.
- Five years provide repeated seasons but only five observations for each market/calendar-month anomaly.
- Holidays, rainfall, tourism, promotions, and local search-engine market share may affect interest.
