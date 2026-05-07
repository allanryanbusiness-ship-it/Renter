# Discovery

This document describes the automatic discovery layer for Renter.

## Architecture

Discovery is intentionally separated from scraping and from generic listing persistence:

| Layer | Files | Responsibility |
|---|---|---|
| Saved searches | `app/services/saved_searches.py`, `SearchCriteria` | Store reusable search criteria and the default Orange County search |
| Provider adapters | `app/sources/discovery.py`, `app/discovery/providers/` | Search approved/local/API-backed providers and normalize candidates |
| Run orchestration | `app/services/discovery.py` | Select providers, run searches, persist run summaries, link listings to runs |
| Persistence and dedupe | `app/services/listings.py` | Create/update listings, preserve user state, score imports |
| API | `app/api/routes.py` | Expose providers, saved searches, discovery runs, and imports |
| Dashboard | `templates/index.html`, `static/js/app.js`, `static/css/styles.css` | Show provider status, saved-search selector, mock discovery, run history, and discovery filters |

## Provider Contract

Every discovery adapter must expose:

- `provider_name`
- `provider_type`
- `is_enabled`
- `requires_api_key`
- `supported_locations`
- `supports_rentals`
- `supports_filters`
- `search(criteria)`
- `normalize(raw_listing)`
- `validate_config()`
- `rate_limit_notes`
- `compliance_notes`

Adapters return normalized listings using the app's canonical schema. Imported listings must preserve `source_name`, `source_type`, `source_url`, `source_listing_id`, `raw_payload_json`, `imported_at`, `first_seen_at`, `last_seen_at`, `discovery_run_id`, and provenance notes.

## Current Providers

| Key | Provider | Enabled by default | Requires key | Notes |
|---|---|---|---|---|
| `mock` | Mock Discovery Provider | No | No | Local demo candidates; dashboard `Mock Discovery` button uses this path |
| `approved_demo_feed` | Approved Demo Provider Feed | Yes | No | Local JSON provider-style feed |
| `rentcast` | RentCast | No | Yes | Real provider API adapter, gracefully skipped when no key is configured |
| `apify` | Apify Placeholder | No | Yes | Disabled placeholder, not implemented |
| `brightdata` | Bright Data Placeholder | No | Yes | Disabled placeholder, not implemented |

## Discovery Run Lifecycle

1. The user selects a saved search and provider set.
2. `POST /api/discovery/run` builds a criteria snapshot.
3. Each provider returns raw records normalized to candidate listings.
4. Dry runs persist candidate previews without importing.
5. Import runs deduplicate by exact source URL and source listing ID.
6. Possible duplicates by address, address + price, or title + city + price are flagged for manual review.
7. New or updated listings are linked to `discovery_run_id`.
8. Scores are recalculated so the ranking queue is immediately usable.
9. `GET /api/discovery/runs` and `GET /api/discovery/runs/{id}` expose run history and details.

## Saved Searches

The default saved search is `Orange County 3BR Yard + Garage`. It targets Orange County, CA, 3+ bedrooms, backyard required, garage required, and allows unknown backyard/garage so weak provider evidence can enter the review queue instead of being silently discarded.

Use:

```bash
curl http://127.0.0.1:8000/api/saved-searches
```

## Configuration

RentCast:

```bash
export RENTAL_DASHBOARD_RENTCAST_ENABLED=true
export RENTCAST_API_KEY=your_key_here
```

Accepted alias:

```bash
export RENTAL_DASHBOARD_RENTCAST_API_KEY=your_key_here
```

Future placeholders:

```bash
APIFY_API_TOKEN=
BRIGHTDATA_API_KEY=
```

Do not store API keys in frontend files, tests, docs, or committed config.

## Adding A Provider

1. Add or reuse an adapter class in `app/sources/discovery.py`.
2. Re-export it from `app/discovery/providers/`.
3. Add provider metadata and compliance/rate-limit notes.
4. Keep it disabled unless config is valid.
5. Normalize source URL, source listing ID, raw payload, feature evidence, and timestamps.
6. Add tests for provider metadata, disabled/missing-key behavior, normalization, dedupe, and endpoint flow.
7. Update `DATA_SOURCES.md`, `SCRAPING_POLICY.md`, `README.md`, and this file.

## Troubleshooting

| Symptom | Check |
|---|---|
| No real provider appears enabled | Confirm API key env vars are set before starting the app |
| RentCast run is skipped | Confirm `RENTAL_DASHBOARD_RENTCAST_ENABLED=true` and `RENTCAST_API_KEY` or `RENTAL_DASHBOARD_RENTCAST_API_KEY` |
| Candidates import as needs review | Backyard or garage evidence is missing/weak and must be verified |
| Duplicate warnings appear | Review possible duplicate listing IDs before contacting or touring |
| Mock discovery imports existing listings | Exact URL/source listing ID dedupe updated existing demo records instead of creating duplicates |

## Compliance Boundaries

Discovery must not implement CAPTCHA bypass, stealth browsing, proxy rotation, bot-detection evasion, credential abuse, or deceptive automation. Listing-site scraping remains unsupported unless a specific source is reviewed, implemented, tested, and documented.
