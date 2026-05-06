# Renter

```text
┌─────────────────────────────────────────────────────────────────────┐
│  Renter                                                            │
│  Orange County rental comparison dashboard                         │
│  FastAPI + SQLite + vanilla JS                                     │
└─────────────────────────────────────────────────────────────────────┘
```

[![Python](https://img.shields.io/badge/python-3.11%2B-3776AB.svg)](#installation)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI-05998B.svg)](#architecture)
[![SQLite](https://img.shields.io/badge/database-SQLite-003B57.svg)](#architecture)
[![License](https://img.shields.io/badge/license-Apache%202.0-D22128.svg)](#license)

Single-page dark-mode dashboard for comparing Orange County, California rental listings with seeded demo data, manual-entry fallback, and a clean path toward compliant source adapters.

Quick run:

```bash
uv sync
uv run python -m app.main
```

Open `http://127.0.0.1:8000`.

## TL;DR

### The Problem

Rental search is fragmented across Zillow, Redfin, Realtor.com, Apartments.com, HotPads, Craigslist, spreadsheets, browser tabs, and manual notes. Even when data is available, every source describes the same property differently, and direct scraping is often brittle or non-compliant.

### The Solution

`Renter` centralizes listings into one canonical schema, ranks them against explicit family-rental criteria, and keeps working even when automation is blocked by allowing manual URL/detail entry.

### Why Use Renter?

| Capability | What it does in this MVP |
|------------|---------------------------|
| Single dashboard | Fullscreen, dark-mode comparison workspace |
| Canonical schema | Normalizes source, location, features, notes, and scoring |
| Seeded demo data | Works immediately on first run |
| Manual fallback | Add a listing URL and details when scraping is unavailable |
| Search criteria | Save Orange County filters and must-haves to SQLite |
| Deal scoring | Ranks price, space, location, features, freshness, and confidence |
| Compliance-first | Risky scrapers are disabled by default |

## Quick Example

```bash
# 1. Install dependencies
uv sync

# 2. Start the app
uv run python -m app.main

# 3. Open the dashboard
xdg-open http://127.0.0.1:8000

# 4. Inspect seeded listings
curl http://127.0.0.1:8000/api/listings | jq '.[0]'

# 5. Read the active search criteria
curl http://127.0.0.1:8000/api/search-criteria | jq

# 6. Inspect score breakdowns
curl http://127.0.0.1:8000/api/scores | jq '.[0]'

# 7. Add a manual listing
curl -X POST http://127.0.0.1:8000/api/listings/manual \
  -H 'content-type: application/json' \
  -d '{
    "title": "Manual Irvine Example",
    "city": "Irvine",
    "price": 4550,
    "bedrooms": 3,
    "bathrooms": 2.5,
    "square_feet": 1820,
    "has_backyard": true,
    "has_garage": true
  }'
```

## Design Philosophy

### 1. Compliance over cleverness

This repo is not built around stealth scraping. It is built around stable product architecture that can accept approved data later.

### 2. Manual fallback is a feature, not a failure

If a user can paste a URL and key details, the dashboard still provides value immediately.

### 3. Normalize early

Different sources use different field names, formats, and confidence levels. The app resolves that before scoring and rendering.

### 4. Score transparently

Deal ranking is decomposed into price, space, location, feature match, freshness, and confidence instead of hiding everything in one opaque number.

### 5. Build the boring foundation first

FastAPI, SQLite, vanilla JS, and explicit modules are enough for the MVP and keep future adapters straightforward.

## Comparison

| Approach | Strengths | Weaknesses | Where Renter fits |
|----------|-----------|------------|-------------------|
| Browser tabs + notes | Fast to start | No normalization, no ranking, hard to compare | Renter replaces this |
| Spreadsheet-only workflow | Flexible | Manual, fragile, low context | Renter can complement later CSV import |
| Direct site scraping | Can automate collection | High breakage and compliance risk | Renter avoids making this the core story |
| Licensed data API | More stable and compliant | Usually paid or gated | Renter is designed to support this path |

## Features

- `GET /api/listings` returns filtered listings plus score breakdowns
- `POST /api/listings/manual` ingests manual entries into the canonical model
- `GET /api/search-criteria` reads the active Orange County criteria
- `POST /api/search-criteria` updates criteria and rescoring
- `GET /api/scores` returns per-listing score details
- Seed data loads automatically into `data/renter.db`

## Installation

### Option 1: `uv` recommended

```bash
uv sync
uv run python -m app.main
```

### Option 2: plain `pip`

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m app.main
```

### Option 3: from source without editable install

```bash
python -m venv .venv
source .venv/bin/activate
pip install fastapi jinja2 pydantic sqlalchemy uvicorn
python -m app.main
```

## Quick Start

1. Clone the repo.
2. Run `uv sync`.
3. Start the server with `uv run python -m app.main`.
4. Visit `http://127.0.0.1:8000`.
5. Review the seeded Orange County listings.
6. Adjust criteria in the left panel.
7. Add a manual listing if a source page cannot be imported safely.

## API Reference

### `GET /api/listings`

Supported query params:

- `county`
- `city`
- `min_bedrooms`
- `require_backyard`
- `require_garage`
- `pets_required`
- `sort_by` with `best_deal`, `price_asc`, `space_desc`, `newest`

Example:

```bash
curl 'http://127.0.0.1:8000/api/listings?min_bedrooms=3&require_backyard=true&require_garage=true&sort_by=best_deal'
```

### `POST /api/listings/manual`

Example:

```bash
curl -X POST http://127.0.0.1:8000/api/listings/manual \
  -H 'content-type: application/json' \
  -d '{
    "title": "Mission Viejo Manual Entry",
    "city": "Mission Viejo",
    "price": 4300,
    "bedrooms": 3,
    "bathrooms": 2.5,
    "has_backyard": true,
    "has_garage": true,
    "note": "Pasted from email thread"
  }'
```

### `GET /api/search-criteria`

```bash
curl http://127.0.0.1:8000/api/search-criteria
```

### `POST /api/search-criteria`

```bash
curl -X POST http://127.0.0.1:8000/api/search-criteria \
  -H 'content-type: application/json' \
  -d '{
    "name": "Orange County Family Rental Search",
    "county": "Orange County",
    "state": "CA",
    "min_bedrooms": 3,
    "min_bathrooms": 2,
    "max_price": 6500,
    "min_sqft": 1400,
    "require_backyard": true,
    "require_garage": true,
    "pets_required": false,
    "notes": "Default MVP criteria",
    "weights": {
      "price": 0.28,
      "space": 0.18,
      "location": 0.18,
      "features": 0.20,
      "freshness": 0.08,
      "confidence": 0.08
    }
  }'
```

### `GET /api/scores`

```bash
curl http://127.0.0.1:8000/api/scores
```

## Architecture

```text
                      ┌──────────────────────────┐
                      │     Source adapters      │
                      │ manual / CSV / future    │
                      └────────────┬─────────────┘
                                   │
                                   v
                      ┌──────────────────────────┐
                      │     Normalization        │
                      │ canonical listing shape  │
                      └────────────┬─────────────┘
                                   │
                                   v
                      ┌──────────────────────────┐
                      │      SQLite models       │
                      │ listings, notes, scores  │
                      └────────────┬─────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    v                             v
          ┌─────────────────────┐       ┌─────────────────────┐
          │ Scoring service     │       │ FastAPI API routes  │
          │ best-deal ranking   │       │ JSON + HTML shell   │
          └────────────┬────────┘       └────────────┬────────┘
                       │                             │
                       └──────────────┬──────────────┘
                                      v
                           ┌─────────────────────┐
                           │ Vanilla JS frontend │
                           │ cards, ranking, table│
                           └─────────────────────┘
```

Detailed docs:

- [ARCHITECTURE.md](ARCHITECTURE.md)
- [PRODUCT_SPEC.md](PRODUCT_SPEC.md)
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)
- [DATA_SOURCES.md](DATA_SOURCES.md)
- [SCRAPING_POLICY.md](SCRAPING_POLICY.md)

## Repository Layout

```text
app/
  api/
  adapters/
  normalization/
  services/
  config.py
  db.py
  main.py
  models.py
  schemas.py
  seed.py
static/
  css/styles.css
  js/app.js
templates/
  index.html
data/
  renter.db            # created on first run
```

## Troubleshooting

### `uv: command not found`

Install `uv` first, or use the `pip` instructions above.

### Dashboard loads but there are no listings

Delete `data/renter.db` and restart the app. The seed bootstrap will recreate the demo database.

### Manual listing POST returns validation errors

Check that JSON numbers are numbers, URLs are valid when provided, and required fields like `title`, `city`, `price`, `bedrooms`, and `bathrooms` are present.

### A live scraper is missing

That is intentional. High-risk scrapers are disabled by default. Read [DATA_SOURCES.md](DATA_SOURCES.md) and [SCRAPING_POLICY.md](SCRAPING_POLICY.md).

### The score feels wrong

Update the active search criteria via the UI or `POST /api/search-criteria`, then refresh listings.

## Limitations

- No auth or multi-user support
- No scheduled background sync jobs
- No live approved API integrations yet
- No CSV ingestion UI yet
- No claim that Zillow, Redfin, Realtor.com, Apartments.com, HotPads, or Craigslist scraping works out of the box

## FAQ

### Does this app scrape Zillow or Redfin right now?

No. The architecture supports future adapters, but risky scrapers are disabled and not represented as working features.

### Why SQLite for the MVP?

It is enough for local comparison workflows, keeps setup trivial, and preserves the domain model needed for later migration.

### Why no React?

The first version is intentionally lean and uses server-delivered HTML plus vanilla JS.

### Can I add my own data source later?

Yes. The repo separates adapters, normalization, persistence, scoring, and API routes specifically to make that safe.

### What happens if I delete the database?

The app recreates the schema and reseeds the demo data on startup.

## About Contributions

*About Contributions:* Please don't take this the wrong way, but I do not accept outside contributions for any of my projects. I simply don't have the mental bandwidth to review anything, and it's my name on the thing, so I'm responsible for any problems it causes; thus, the risk-reward is highly asymmetric from my perspective. I'd also have to worry about other "stakeholders," which seems unwise for tools I mostly make for myself for free. Feel free to submit issues, and even PRs if you want to illustrate a proposed fix, but know I won't merge them directly. Instead, I'll have Claude or Codex review submissions via `gh` and independently decide whether and how to address them. Bug reports in particular are welcome. Sorry if this offends, but I want to avoid wasted time and hurt feelings. I understand this isn't in sync with the prevailing open-source ethos that seeks community contributions, but it's the only way I can move at this velocity and keep my sanity.

## License

Licensed under Apache License 2.0. See [LICENSE](LICENSE).
