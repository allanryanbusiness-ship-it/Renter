# Renter

```text
┌────────────────────────────────────────────────────────────────────┐
│  Renter                                                           │
│  Local-first Orange County rental comparison command center       │
│  FastAPI + SQLite + vanilla HTML/CSS/JS                           │
└────────────────────────────────────────────────────────────────────┘
```

[![Python](https://img.shields.io/badge/python-3.11%2B-3776AB.svg)](#install)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI-05998B.svg)](#architecture)
[![SQLite](https://img.shields.io/badge/database-SQLite-003B57.svg)](#daily-local-use)
[![License](https://img.shields.io/badge/license-Apache%202.0-D22128.svg)](#license)

Renter helps compare Orange County, California rental listings for a specific search: 3+ bedrooms, backyard required, garage required, and strong value potential. It is a fullscreen dark-mode dashboard with browser clipping, safe manual imports, explainable scoring, market benchmarks, backup/export/restore, and local SQLite persistence.

```bash
uv sync
uv run python run_local.py
```

Open `http://127.0.0.1:8000`.

## Why

Rental hunting quickly turns into scattered tabs, screenshots, notes, duplicate listings, and vague price intuition. Renter turns that into a local command center:

| Problem | Renter's Answer |
|---|---|
| Listings are scattered across Zillow, Redfin, Realtor.com, Apartments.com, HotPads, Craigslist, Facebook Marketplace, property manager sites, and spreadsheets | Capture them into one normalized local database |
| Automated scraping is brittle or risky | Use provider-based discovery, mock/demo discovery, user-driven browser clips, paste import, CSV import, manual entry, and URL references |
| "Good deal" is hard to judge | Compare rent against editable Orange County 3-bedroom city benchmarks |
| Notes and decisions get lost | Track notes, watchlist status, decision status, priority, next action, and source provenance |
| Local data feels fragile | Use a stable DB path, timestamped backups, JSON/CSV exports, and merge-only restores |

## Current Capabilities

| Area | What Works |
|---|---|
| Dashboard | Single-page fullscreen dark UI with ranking queue, property cards, details, comparison table, and system panel |
| Automatic discovery | Runs saved searches through mock or approved/provider-based adapters, imports candidates, deduplicates, scores, and flags review needs |
| Browser clipper | Bookmarklet captures current URL, title, selected text, source domain, timestamp, and user note |
| Fallback import | Bookmarklet copies JSON if direct POST is blocked; dashboard can import that payload |
| Manual entry | Add structured listings by hand |
| Paste import | Deterministic parser extracts price, beds, baths, sqft, address, city, backyard/garage evidence, parking, pets, laundry, and AC |
| CSV import | Imports user-controlled CSV text/files and preserves unknown columns |
| URL reference | Saves listing URL and notes without fetching or scraping the page |
| Duplicate handling | Exact source URL updates existing listings; possible duplicates are flagged for review |
| Scoring | Explains match, deal, confidence, completeness, freshness, source reliability, benchmark delta, warnings, and next actions |
| Benchmarks | Editable 3-bedroom city benchmark JSON with source notes and confidence labels |
| Reliability | Backup, export JSON, export CSV, full JSON export, merge restore, data quality checks, and local logs |

## Quick Start

```bash
# 1. Install dependencies
uv sync

# 2. Verify runtime paths
uv run python run_local.py --check

# 3. Start the dashboard
uv run python run_local.py

# 4. Open the app
xdg-open http://127.0.0.1:8000
```

The first startup creates `data/renter.db` and seeds demo listings so the dashboard is useful immediately.

## Daily Workflow

1. Start Renter with `uv run python run_local.py`.
2. Open `http://127.0.0.1:8000`.
3. Run `Mock Discovery` or a configured provider search from the Automatic Discovery panel.
4. Drag `Clip to Renter` from the Browser Clipper panel to your bookmarks bar.
5. Browse rental listings normally.
6. Select useful listing text and click the bookmarklet.
7. If direct import is blocked, paste the copied fallback JSON into the dashboard.
8. Review score reasons, benchmark delta, backyard/garage evidence, source URL, duplicate warnings, and next action.
9. Back up from the System panel before or after a serious search session.

## Install

### Recommended: `uv`

```bash
uv sync
uv run python run_local.py
```

### Plain `pip`

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python run_local.py
```

### Platform scripts

```bash
./start.sh
```

```bat
start.bat
```

## Daily Local Use

`run_local.py` prints the resolved dashboard URL, database path, backup folder, and log folder.

Default paths:

| Item | Default |
|---|---|
| Dashboard | `http://127.0.0.1:8000` |
| Database | `data/renter.db` |
| Backups | `backups/` |
| Logs | `logs/renter.log` |

Environment overrides:

```bash
export RENTAL_DASHBOARD_DB_PATH=/absolute/path/renter.db
export RENTAL_DASHBOARD_BACKUP_DIR=/absolute/path/backups
export RENTAL_DASHBOARD_LOG_DIR=/absolute/path/logs
export RENTAL_DASHBOARD_HOST=127.0.0.1
export RENTAL_DASHBOARD_PORT=8000
export RENTAL_DASHBOARD_APPROVED_FEED_PATH=/absolute/path/approved_provider_feed.json
export RENTAL_DASHBOARD_DISCOVERY_DEFAULT_CITIES=Irvine,Tustin,Lake Forest,Costa Mesa
export RENTAL_DASHBOARD_PROVIDER_API_URL=
export RENTAL_DASHBOARD_PROVIDER_API_KEY=
export RENTAL_DASHBOARD_PROVIDER_API_NAME=Approved JSON Provider API
# APIFY_API_TOKEN and BRIGHTDATA_API_KEY are reserved for disabled placeholders.
```

Use an absolute `RENTAL_DASHBOARD_DB_PATH` for long-running daily use if the repo may be moved.

## Automatic Discovery

Automatic discovery uses approved/provider-based adapters only. The dashboard ships with a default saved search named `Orange County 3BR Yard + Garage`, a mock provider, and a local approved provider feed so the complete workflow works without external calls.

Current provider keys:

| Key | Status | Network | Notes |
|---|---|---|---|
| `mock` | Works without credentials | No | Demo/mock Orange County rental candidates for dashboard testing |
| `approved_demo_feed` | Works without credentials | No | Reads [app/data/approved_provider_feed.json](app/data/approved_provider_feed.json) |
| `approved_json_api` | Disabled until configured | Yes, approved provider/feed API only | Generic adapter for a user-approved JSON endpoint |
| `apify` | Placeholder only | No | Disabled pending compliance review and implementation |
| `brightdata` | Placeholder only | No | Disabled pending compliance review and implementation |

Run discovery from the dashboard's `Automatic Discovery` panel, or call the API:

```bash
curl -X POST http://127.0.0.1:8000/api/discovery/run \
  -H 'content-type: application/json' \
  -d '{"provider_keys":["mock"],"limit":25}'
```

Use `dry_run` to preview candidates without importing:

```bash
curl -X POST http://127.0.0.1:8000/api/discovery/run \
  -H 'content-type: application/json' \
  -d '{"provider_keys":["mock"],"limit":10,"dry_run":true,"import_results":false}'
```

Optional approved JSON API discovery is available but disabled unless configured:

```bash
export RENTAL_DASHBOARD_PROVIDER_API_URL=https://your-approved-provider.example/listings
export RENTAL_DASHBOARD_PROVIDER_API_KEY=...
export RENTAL_DASHBOARD_PROVIDER_API_NAME="Approved Property Feed"
```

Discovery candidates are normalized, exact source URL/source listing ID duplicates update existing listings, possible duplicates are marked for review, user notes/decision/watchlist state are preserved on updates, and scores are recalculated after import. Backyard and garage fields are inferred from explicit provider fields plus descriptions/amenities and weak evidence is marked for review. See [DISCOVERY.md](DISCOVERY.md) and [AUTOMATIC_LISTING_DISCOVERY.md](AUTOMATIC_LISTING_DISCOVERY.md).

## Browser Clipper

The browser clipper is user-driven capture, not scraping.

What it captures:

| Field | Source |
|---|---|
| `source_url` | Current page URL |
| `page_title` | Browser document title |
| `selected_text` | Text selected by the user |
| `page_text` | Limited visible text fallback when nothing is selected |
| `source_domain` | Current hostname |
| `user_notes` | Optional prompt note |
| `captured_at` | Browser timestamp |

Direct import target:

```text
POST http://127.0.0.1:8000/api/import/clip
```

Some sites or browsers block cross-origin bookmarklet requests. In that case the bookmarklet copies structured JSON and opens the dashboard with a fallback payload. Paste it into `Fallback clipped JSON` and click `Import Browser Clip`.

See [BOOKMARKLET.md](BOOKMARKLET.md) for installation and troubleshooting.

## Backup, Export, Restore

Create a timestamped SQLite backup:

```bash
curl -X POST http://127.0.0.1:8000/api/admin/backup
```

Export data:

```bash
curl http://127.0.0.1:8000/api/export/listings.json -o renter_listings.json
curl http://127.0.0.1:8000/api/export/listings.csv -o renter_listings.csv
curl http://127.0.0.1:8000/api/export/full.json -o renter_full.json
```

Merge-import a prior full export:

```bash
curl -X POST http://127.0.0.1:8000/api/import/full-json \
  -H 'content-type: application/json' \
  --data-binary @renter_full.json
```

Restore is intentionally merge-only. It does not wipe your current database.

Check system and data quality:

```bash
curl http://127.0.0.1:8000/api/admin/status
curl http://127.0.0.1:8000/api/admin/data-quality
```

See [OPERATIONS.md](OPERATIONS.md) for daily use, backup, restore, benchmark update, and safe shutdown details.

## API Reference

| Endpoint | Purpose |
|---|---|
| `GET /api/listings` | List filtered/ranked listings with score breakdowns |
| `POST /api/listings/manual` | Add a structured manual listing |
| `POST /api/import/clip` | Import a browser clip payload |
| `POST /api/import/paste` | Import user-pasted listing text |
| `POST /api/import/csv` | Import CSV text |
| `POST /api/listings/url-reference` | Save a URL without fetching it |
| `GET /api/discovery/providers` | List configured discovery providers |
| `POST /api/discovery/run` | Run approved/provider-based automatic discovery |
| `GET /api/discovery/runs` | Read persisted discovery run history |
| `GET /api/discovery/runs/{id}` | Read one discovery run with criteria snapshot and candidate preview |
| `GET /api/saved-searches` | List saved discovery/search criteria |
| `POST /api/saved-searches` | Create saved discovery/search criteria |
| `PUT /api/saved-searches/{id}` | Update saved discovery/search criteria |
| `DELETE /api/saved-searches/{id}` | Deactivate a saved search |
| `GET /api/listings/{id}/score-breakdown` | Read one listing's scoring explanation |
| `PATCH /api/listings/{id}/decision` | Update decision, priority, and next action |
| `PATCH /api/listings/{id}/notes` | Add a note |
| `PATCH /api/listings/{id}/watchlist` | Update watchlist state |
| `GET /api/search-criteria` | Read active search criteria |
| `POST /api/search-criteria` | Update search criteria and rescore |
| `GET /api/scores` | Read all score breakdowns |
| `POST /api/admin/backup` | Create a SQLite backup |
| `GET /api/admin/status` | Read local status |
| `GET /api/admin/data-quality` | Read missing-field, duplicate, score, and benchmark checks |
| `GET /api/export/listings.json` | Export listings JSON |
| `GET /api/export/listings.csv` | Export listings CSV |
| `GET /api/export/full.json` | Export listings, sources, discovery audit state, scores, criteria, and benchmarks |
| `POST /api/import/full-json` | Merge-import a prior full JSON export |

Example manual listing:

```bash
curl -X POST http://127.0.0.1:8000/api/listings/manual \
  -H 'content-type: application/json' \
  -d '{
    "title": "Irvine Manual Example",
    "city": "Irvine",
    "price": 4550,
    "bedrooms": 3,
    "bathrooms": 2.5,
    "square_feet": 1820,
    "has_backyard": true,
    "has_garage": true
  }'
```

Example browser clip:

```bash
curl -X POST http://127.0.0.1:8000/api/import/clip \
  -H 'content-type: application/json' \
  -d '{
    "source_url": "https://www.redfin.com/CA/Irvine/example",
    "page_title": "3 Bed Home in Irvine",
    "selected_text": "$4,650/mo 3 beds 2.5 baths 1850 sqft fenced backyard attached garage Irvine CA 92620",
    "source_domain": "redfin.com",
    "user_notes": "Clip captured while browsing",
    "captured_at": "2026-05-06T12:00:00Z"
  }'
```

## Scoring

Renter ranks listings with transparent score components:

| Score | Meaning |
|---|---|
| `match_score` | Fit against Orange County, 3+ bedrooms, backyard, and garage criteria |
| `deal_score` | Rent versus city benchmark, typical range, price/bedroom, price/sqft, space, freshness, confidence, and completeness |
| `confidence_score` | Source confidence plus evidence completeness |
| `completeness_score` | Presence of key fields like price, city, sqft, backyard, garage, source URL, and raw text |
| `source_reliability_score` | Confidence by source type |

Benchmark labels:

| Label | Interpretation |
|---|---|
| `below_typical_low` | Potentially strong value, but verify quality, fees, and scam risk |
| `below_market` | Below the editable city 3-bedroom benchmark |
| `near_market` | Fair versus the city benchmark range |
| `above_typical_high` | Expensive unless features/location justify it |

Benchmark assumptions live in [app/data/city_benchmarks.json](app/data/city_benchmarks.json), with research notes in [MARKET_RESEARCH.md](MARKET_RESEARCH.md).

Validate benchmark edits:

```bash
uv run pytest tests/test_benchmarks.py tests/test_deal_score_calibration.py tests/test_scoring.py
```

## Architecture

```text
Browser/manual/CSV/paste input
        │
        v
┌────────────────────┐
│ Source adapters    │  safe ingestion only
└─────────┬──────────┘
          v
┌────────────────────┐
│ Normalization      │  canonical listing fields
└─────────┬──────────┘
          v
┌────────────────────┐
│ SQLite persistence │  listings, notes, sources, scores
└─────────┬──────────┘
          v
┌────────────────────┐
│ Scoring + quality  │  benchmarks, ranking, warnings
└─────────┬──────────┘
          v
┌────────────────────┐
│ FastAPI + vanilla  │  fullscreen local dashboard
└────────────────────┘
```

Key modules:

| Path | Responsibility |
|---|---|
| `app/api/routes.py` | Dashboard API |
| `app/services/listings.py` | Persistence, imports, serialization, scoring sync |
| `app/services/scoring.py` | Ranking and explanation logic |
| `app/services/benchmark_service.py` | Benchmark loading, validation, fallback |
| `app/services/reliability.py` | Backup, export, restore, status, data quality |
| `app/sources/` | Safe ingestion adapters |
| `templates/index.html` | Dashboard shell |
| `static/js/app.js` | Frontend state and API calls |
| `static/css/styles.css` | Dark command-center styling |
| `static/js/bookmarklet.js` | Browser clipper source |

## Data and Compliance

Renter does not implement live Zillow, Redfin, Realtor.com, Apartments.com, HotPads, Craigslist, or Facebook Marketplace scraping. High-risk scrapers are disabled placeholders unless a future source-specific review approves a compliant path.

Allowed current ingestion paths:

| Path | Server fetches external listing page? |
|---|---|
| Manual entry | No |
| Mock discovery provider | No |
| Automatic local provider feed | No |
| Approved JSON provider API | No listing-site page fetch; calls a configured provider/feed API only |
| Apify/Bright Data placeholders | No, disabled placeholders only |
| Browser clipper | No |
| Paste import | No |
| CSV import | No |
| URL reference | No |

Read [SCRAPING_POLICY.md](SCRAPING_POLICY.md) and [DATA_SOURCES.md](DATA_SOURCES.md) before adding any source integration.

## Repository Layout

```text
app/
  api/
  data/
    approved_provider_feed.json
  services/
  sources/
static/
  css/styles.css
  js/app.js
  js/bookmarklet.js
templates/
  index.html
backups/
exports/
logs/
data/
  renter.db
run_local.py
start.sh
start.bat
```

## Documentation

| Document | Purpose |
|---|---|
| [OPERATIONS.md](OPERATIONS.md) | Daily use, backups, restore, quality checks, safe shutdown |
| [DISCOVERY.md](DISCOVERY.md) | Discovery architecture, provider interface, saved searches, lifecycle, troubleshooting |
| [AUTOMATIC_LISTING_DISCOVERY.md](AUTOMATIC_LISTING_DISCOVERY.md) | Approved/provider-based discovery workflow |
| [AUDIT_AUTOMATIC_LISTING_DISCOVERY.md](AUDIT_AUTOMATIC_LISTING_DISCOVERY.md) | Implementation audit for automatic discovery |
| [BOOKMARKLET.md](BOOKMARKLET.md) | Browser clipper install/use/fallback |
| [MARKET_RESEARCH.md](MARKET_RESEARCH.md) | Benchmark sources and limitations |
| [DATA_SOURCES.md](DATA_SOURCES.md) | Source strategy and research landscape |
| [DATA_SOURCE_MATRIX.md](DATA_SOURCE_MATRIX.md) | Source risk/utility matrix |
| [SCRAPING_POLICY.md](SCRAPING_POLICY.md) | Compliance and ingestion policy |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Module boundaries and data flow |
| [PRODUCT_SPEC.md](PRODUCT_SPEC.md) | Product intent and MVP scope |
| [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) | Build plan |
| [AGENTS.md](AGENTS.md) | Rules for future coding agents |

## Troubleshooting

| Symptom | Fix |
|---|---|
| `uv: command not found` | Install `uv`, or use the plain `pip` install path |
| Dashboard starts with only demo listings | Check `RENTAL_DASHBOARD_DB_PATH`; you may be pointing at a different SQLite file |
| Browser clip direct import fails | Use the fallback JSON copied by the bookmarklet |
| Paste import misses a field | Select/paste cleaner listing text, then verify evidence manually |
| CSV import skips rows | Read the returned `errors`; city, price, bedrooms, and bathrooms are required |
| Backup fails | Check that `backups/` or `RENTAL_DASHBOARD_BACKUP_DIR` is writable |
| Score looks wrong | Review search criteria and [app/data/city_benchmarks.json](app/data/city_benchmarks.json) |

## Limitations

- No auth or multi-user support.
- No scheduled background sync jobs.
- No listing edit UI yet.
- No screenshot or attachment storage yet.
- Docker support is intentionally skipped; local Python is the supported daily path.
- Browser clips depend on selected text quality and still require manual backyard/garage verification.
- Market benchmarks are public-source estimates and can lag real asking rents.
- City benchmarks are apartment-oriented where public 3-bedroom house data was not safely available.
- No claim that live Zillow, Redfin, Realtor.com, Apartments.com, HotPads, Craigslist, or Facebook Marketplace scraping works.

## FAQ

### Does Renter scrape Zillow or Redfin?

No. It stores user-provided or user-triggered data. The server does not fetch protected listing pages.

### What source path should I use daily?

Use the browser clipper first. Use paste import when the clipper captures messy text, CSV for spreadsheet data, manual entry for known details, and URL reference when you only want to save a link.

### Where is my data?

By default, in `data/renter.db`. Use `RENTAL_DASHBOARD_DB_PATH` to pin it somewhere else.

### How do I avoid losing data?

Use the System panel backup button, export `full.json`, and keep the SQLite backup files under `backups/`.

### Why SQLite?

It is enough for a local command center, easy to back up, and keeps daily setup simple.

### Why no React?

The MVP intentionally uses server-delivered HTML plus vanilla JS to keep setup and maintenance small.

### Can I add a source adapter later?

Yes, but preserve provenance and compliance rules. Do not add stealth scraping, CAPTCHA bypass, or proxy evasion.

## About Contributions

*About Contributions:* Please don't take this the wrong way, but I do not accept outside contributions for any of my projects. I simply don't have the mental bandwidth to review anything, and it's my name on the thing, so I'm responsible for any problems it causes; thus, the risk-reward is highly asymmetric from my perspective. I'd also have to worry about other "stakeholders," which seems unwise for tools I mostly make for myself for free. Feel free to submit issues, and even PRs if you want to illustrate a proposed fix, but know I won't merge them directly. Instead, I'll have Claude or Codex review submissions via `gh` and independently decide whether and how to address them. Bug reports in particular are welcome. Sorry if this offends, but I want to avoid wasted time and hurt feelings. I understand this isn't in sync with the prevailing open-source ethos that seeks community contributions, but it's the only way I can move at this velocity and keep my sanity.

## License

Licensed under Apache License 2.0. See [LICENSE](LICENSE).
