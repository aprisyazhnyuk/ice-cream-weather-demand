# Google Trends export procedure

Google Trends permits official CSV exports from the **Interest over time** chart. The project intentionally imports those exports rather than depending on an unofficial scraper.

## Fixed query

- Topic: **Ice cream** (`/m/0cxn2`)
- Search type: Web Search
- Category: All categories
- Period: 2021-01-01 through 2025-12-31
- One export per market geography

## Export checklist

For each row below:

1. Open the query link.
2. Confirm that the location displayed by Google Trends matches the target geography.
3. In **Interest over time**, select Download CSV.
4. Save the file under the exact repository path shown.
5. Do not edit the contents of the raw export.

| Market | Trends geography | Query | Save as |
|---|---|---|---|
| Toronto | Ontario | [Open](https://trends.google.com/trends/explore?date=2021-01-01%202025-12-31&geo=CA-ON&q=%2Fm%2F0cxn2) | `data/raw/google_trends/toronto.csv` |
| London | Greater London | [Open](https://trends.google.com/trends/explore?date=2021-01-01%202025-12-31&geo=GB-LND&q=%2Fm%2F0cxn2) | `data/raw/google_trends/london.csv` |
| Rome | Lazio | [Open](https://trends.google.com/trends/explore?date=2021-01-01%202025-12-31&geo=IT-62&q=%2Fm%2F0cxn2) | `data/raw/google_trends/rome.csv` |
| Tokyo | Tokyo | [Open](https://trends.google.com/trends/explore?date=2021-01-01%202025-12-31&geo=JP-13&q=%2Fm%2F0cxn2) | `data/raw/google_trends/tokyo.csv` |
| Delhi | Delhi | [Open](https://trends.google.com/trends/explore?date=2021-01-01%202025-12-31&geo=IN-DL&q=%2Fm%2F0cxn2) | `data/raw/google_trends/delhi.csv` |
| Singapore | Singapore | [Open](https://trends.google.com/trends/explore?date=2021-01-01%202025-12-31&geo=SG&q=%2Fm%2F0cxn2) | `data/raw/google_trends/singapore.csv` |
| São Paulo | São Paulo | [Open](https://trends.google.com/trends/explore?date=2021-01-01%202025-12-31&geo=BR-SP&q=%2Fm%2F0cxn2) | `data/raw/google_trends/sao_paulo.csv` |
| Sydney | New South Wales | [Open](https://trends.google.com/trends/explore?date=2021-01-01%202025-12-31&geo=AU-NSW&q=%2Fm%2F0cxn2) | `data/raw/google_trends/sydney.csv` |
| Johannesburg | Gauteng | [Open](https://trends.google.com/trends/explore?date=2021-01-01%202025-12-31&geo=ZA-GT&q=%2Fm%2F0cxn2) | `data/raw/google_trends/johannesburg.csv` |
| Moscow | Moscow | [Open](https://trends.google.com/trends/explore?date=2021-01-01%202025-12-31&geo=RU-MOW&q=%2Fm%2F0cxn2) | `data/raw/google_trends/moscow.csv` |

If Google Trends rejects a geography code or reports insufficient data, record the displayed message before selecting a broader fallback. Do not silently substitute a national series.

## Import

After all ten files are present:

```bash
.venv/bin/python scripts/import_google_trends.py
```

The importer detects Google’s metadata row and source resolution, converts `<1` observations to 0.5 with a separate quality flag, day-weights weekly values across calendar months, and requires exactly 60 monthly observations per market.
