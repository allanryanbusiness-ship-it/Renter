# Architecture

## Design Principles

- Keep ingestion separate from the app core.
- Normalize every source into one canonical listing shape.
- Score listings against explicit search criteria.
- Store source lineage and run history, even in the MVP.
- Prefer compliant and licensed data paths over brittle scraping.

## Module Boundaries

### `app/sources/`

- `base.py` defines the active ingestion contract.
- `manual.py`, `paste_import.py`, `csv_import.py`, and `url_reference.py` implement supported MVP data paths.
- `discovery.py` implements approved/provider-based automatic discovery adapters.
- `experimental_scraper_placeholder.py` provides disabled-by-default placeholders for high-risk future scrapers.
- Adapters return normalized listings plus provenance metadata; they do not write to the database directly.

### `app/discovery/`

- `base.py` documents the provider adapter contract required by discovery integrations.
- `adapters.py` exposes approved/provider-based discovery adapters.
- `providers/` re-exports the mock, approved JSON API, Apify placeholder, and Bright Data placeholder adapters.
- `service.py` provides package-level aliases for discovery orchestration.
- `persistence.py` persists discovery provider metadata and discovery run audit rows.
- The package boundary keeps discovery orchestration separate from manual, CSV, paste, URL, and browser-clip ingestion.

### `app/normalization/`

- Converts raw or pasted data into canonical listing fields.
- Centralizes boolean coercion, URL cleanup, notes extraction, and feature normalization.

### `app/models.py`

SQLite-backed entities:

- `Source`
- `ImportRun`
- `DiscoveryProvider`
- `DiscoveryRun`
- `Listing`
- `ListingScore`
- `SearchCriteria`
- `ListingNote`
- `WatchlistEntry`

The listing model captures normalized source provenance, raw import text/payloads, tri-state backyard/garage status, evidence strings, `discovery_run_id`, and stored match/deal/confidence scores.

### `app/services/`

- `listings.py` orchestrates reads, filters, manual writes, criteria updates, and rescoring.
- `discovery.py` orchestrates provider discovery, active-criteria filtering, dry runs, imports, and provider metadata.
- `saved_searches.py` manages saved discovery/search criteria and the default Orange County saved search.
- `deduplication_service.py` documents shared exact/possible duplicate rules.
- `discovery_run_service.py` re-exports discovery run orchestration for provider-facing imports.
- `benchmark_service.py` loads editable city benchmarks, validates shape, normalizes city names, and provides county fallback context.
- `reliability.py` owns SQLite backups, JSON/CSV exports, merge-import restore, system status, and data-quality checks.
- `scoring.py` computes score breakdowns and ranking explanations.

### `app/api/routes.py`

Exposes the JSON contract consumed by the dashboard:

- `GET /api/listings`
- `POST /api/listings/manual`
- `POST /api/import/paste`
- `POST /api/import/clip`
- `POST /api/import/csv`
- `POST /api/listings/url-reference`
- `GET /api/discovery/providers`
- `POST /api/discovery/run`
- `GET /api/discovery/runs`
- `GET /api/discovery/runs/{id}`
- `GET /api/saved-searches`
- `POST /api/saved-searches`
- `PUT /api/saved-searches/{id}`
- `DELETE /api/saved-searches/{id}`
- `GET /api/listings/{id}/score-breakdown`
- `PATCH /api/listings/{id}/decision`
- `PATCH /api/listings/{id}/notes`
- `PATCH /api/listings/{id}/watchlist`
- `GET /api/search-criteria`
- `POST /api/search-criteria`
- `GET /api/scores`
- `GET /api/admin/status`
- `POST /api/admin/backup`
- `GET /api/admin/data-quality`
- `GET /api/export/listings.json`
- `GET /api/export/listings.csv`
- `GET /api/export/full.json`
- `POST /api/import/full-json`

### Frontend

- `templates/index.html` renders the app shell.
- `static/js/app.js` manages fetches, UI state, rendering, and form submissions.
- `static/js/bookmarklet.js` is the user-triggered browser clipper source used to generate the dashboard bookmarklet.
- `static/css/styles.css` handles the full-screen dashboard styling.

## Data Flow

1. A source adapter yields raw listing data, provider candidates, a browser clip payload, or manual entry.
2. The normalization layer converts it into canonical fields.
3. Persistence stores the listing plus source and import-run metadata.
4. Discovery imports update exact source URL or source listing ID duplicates and flag possible duplicates for review.
5. The scoring service recomputes ranking against the active search criteria and editable market benchmarks.
6. API routes return listings and scores to the frontend.
7. The frontend renders cards, ranking, and the comparison table.

## Future Extensions

- Scheduled refresh jobs per adapter
- More licensed API integrations
- Listing history snapshots
- Alerts and watchlist workflows
