# When Does Ice Cream Season Start?

An interactive data-visualization project exploring how outdoor temperature relates to Google search interest in ice cream across climates and hemispheres.

The project is designed as a BI/data-engineering portfolio piece: source data is documented, transformations are reproducible, analytical limitations are explicit, and the final visualization can be hosted directly with GitHub Pages.

## Research question

At what temperature does interest in ice cream begin to rise in different markets?

Google Trends is treated as a **demand-intent proxy**, not a measure of units sold. Country-level results compare relative seasonal response, not absolute demand volumes.

## Initial coverage

The comparison uses ten metropolitan regions across Canada, the United Kingdom, Italy, Japan, India, Singapore, Brazil, Australia, South Africa, and Russia. Local search-interest geography is paired with local weather coordinates wherever Google Trends supports it. London is the documented exception: England interest is paired with London weather as the narrowest available proxy.

Moscow (`RU-MOW`) is included as a highlighted Central Russia deep dive.

## Data

- Google Trends: weekly interest in the language-independent **Ice cream** topic, aggregated to monthly values.
- Open-Meteo ERA5-Land: daily metropolitan weather, aggregated to the same period as Trends.
- Analysis window: complete calendar years 2021–2025.

See [docs/data-sources.md](docs/data-sources.md) for the source assessment and methodological constraints.

## Repository structure

```text
assets/                 Browser styles and visualization code
config/markets.csv      Market definitions and source geography codes
data/raw/               Immutable source snapshots
data/processed/         Web-ready analytical datasets
docs/                   Data definitions and methodology
scripts/                Reproducible ingestion and transformation scripts
tests/                  Data-contract tests
index.html               GitHub Pages entry point
```

## Local setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
python3 -m http.server 8000
```

Then open `http://localhost:8000`.

Run the current data-contract check with:

```bash
python3 scripts/validate_markets.py
```

Download and aggregate all ten weather series with:

```bash
.venv/bin/python scripts/fetch_weather.py
```

Follow [docs/google-trends-export.md](docs/google-trends-export.md) to acquire and validate the ten official Trends exports.

## Project status

- [x] Dataset feasibility assessment
- [x] Repository and environment scaffold
- [x] Metropolitan market list plus Moscow regional deep dive
- [x] Acquire and validate ERA5-Land temperature data
- [ ] Acquire and snapshot Google Trends data
- [ ] Build analytical model and insight table
- [ ] Build and test the interactive visualization
- [ ] Publish with GitHub Pages

## Attribution

Data source: Google Trends. Weather data is attributed to Open-Meteo and Copernicus/ECMWF ERA5-Land.
