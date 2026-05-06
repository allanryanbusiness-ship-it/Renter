# Architecture

## Design Principles

- Keep ingestion separate from the app core.
- Normalize every source into one canonical listing shape.
- Score listings against explicit search criteria.
- Store source lineage and run history, even in the MVP.
- Prefer compliant and licensed data paths over brittle scraping.

## Module Boundaries

### `app/adapters/`

- `base.py` defines the adapter contract.
- High-risk site scrapers are represented as disabled placeholders.
- Manual entry is treated as a first-class adapter path.

### `app/normalization/`

- Converts raw or pasted data into canonical listing fields.
- Centralizes boolean coercion, URL cleanup, notes extraction, and feature normalization.

### `app/models.py`

SQLite-backed entities:

- `Source`
- `ImportRun`
- `Listing`
- `ListingScore`
- `SearchCriteria`
- `ListingNote`
- `WatchlistEntry`

### `app/services/`

- `listings.py` orchestrates reads, filters, manual writes, criteria updates, and rescoring.
- `scoring.py` computes score breakdowns and ranking explanations.

### `app/api/routes.py`

Exposes the JSON contract consumed by the dashboard:

- `GET /api/listings`
- `POST /api/listings/manual`
- `GET /api/search-criteria`
- `POST /api/search-criteria`
- `GET /api/scores`

### Frontend

- `templates/index.html` renders the app shell.
- `static/js/app.js` manages fetches, UI state, rendering, and form submissions.
- `static/css/styles.css` handles the full-screen dashboard styling.

## Data Flow

1. A source adapter yields raw listing data or manual entry.
2. The normalization layer converts it into canonical fields.
3. Persistence stores the listing plus source and import-run metadata.
4. The scoring service recomputes ranking against the active search criteria.
5. API routes return listings and scores to the frontend.
6. The frontend renders cards, ranking, and the comparison table.

## Future Extensions

- Scheduled refresh jobs per adapter
- CSV ingestion adapters
- Licensed API integrations
- Listing history snapshots
- Alerts and watchlist workflows

