# Automatic Listing Discovery

Automatic discovery imports rental candidates through approved/provider-based adapters. It does not scrape Zillow, Redfin, Realtor.com, Apartments.com, HotPads, Craigslist, Facebook Marketplace, or other listing pages.

## What Works Now

| Provider | Key | Status | External network? | Use |
|---|---|---|---|---|
| Mock Discovery Provider | `mock` | Available without credentials | No | Realistic demo Orange County rental candidates for dashboard use, tests, and local workflow demos |
| Approved Demo Provider Feed | `approved_demo_feed` | Available without credentials | No | Local provider-style JSON feed for testing normalization, dedupe, scoring, and run history |
| Approved JSON Provider API | `approved_json_api` | Disabled until configured | Yes, approved provider/feed API only | Generic adapter for a reviewed JSON endpoint |
| Apify Placeholder | `apify` | Not implemented | No | Disabled placeholder for future reviewed Apify actor integration |
| Bright Data Placeholder | `brightdata` | Not implemented | No | Disabled placeholder for future reviewed Bright Data integration |

The local feed lives at [app/data/approved_provider_feed.json](app/data/approved_provider_feed.json). It is intentionally local demo data, not proof that any live listing-site scraping works.

## API

List providers:

```bash
curl http://127.0.0.1:8000/api/discovery/providers
```

List saved searches:

```bash
curl http://127.0.0.1:8000/api/saved-searches
```

Run mock discovery and import matches:

```bash
curl -X POST http://127.0.0.1:8000/api/discovery/run \
  -H 'content-type: application/json' \
  -d '{"provider_keys":["mock"],"limit":25}'
```

Dry run without importing:

```bash
curl -X POST http://127.0.0.1:8000/api/discovery/run \
  -H 'content-type: application/json' \
  -d '{"provider_keys":["mock"],"limit":10,"dry_run":true,"import_results":false}'
```

Run a saved search:

```bash
curl -X POST http://127.0.0.1:8000/api/discovery/run \
  -H 'content-type: application/json' \
  -d '{"saved_search_id":1,"provider_keys":["mock"],"limit":25}'
```

Read run history and one run:

```bash
curl http://127.0.0.1:8000/api/discovery/runs
curl http://127.0.0.1:8000/api/discovery/runs/1
```

Full exports include discovery audit state:

```bash
curl http://127.0.0.1:8000/api/export/full.json -o renter_full.json
```

The full JSON payload includes `discovery_providers`, recent `discovery_runs`, and imported listings with `discovery_run_id`.

## Discovery Flow

1. A saved search supplies county, state, city list, ZIP codes, bedrooms, price, backyard/garage requirements, property types, and provider names.
2. Selected provider adapters search approved/local/API-backed sources only.
3. Provider records are normalized to the canonical listing shape with source URL, source listing ID, raw payload, imported timestamp, first/last seen timestamps, and provenance notes.
4. Explicit provider fields plus description, amenities, parking, and raw text are parsed for backyard and garage evidence.
5. Exact source URL or source listing ID matches update the existing listing.
6. Possible duplicates by normalized address, address + price, or title + city + price are imported and marked for review.
7. User notes, decision status, watchlist status, and private notes are preserved during exact duplicate updates.
8. Import runs and discovery runs are persisted with counts, warnings, errors, candidate previews, and imported listing IDs.
9. Imported/updated listings are linked back to `discovery_run_id`.
10. Scores are recalculated immediately and the dashboard refreshes the ranking/review queue.

## Default Saved Search

Startup creates a saved search named `Orange County 3BR Yard + Garage` if it is missing. It targets Orange County, CA with 3+ bedrooms, backyard required, garage required, unknown backyard/garage allowed for review, and the default city list:

Irvine, Costa Mesa, Huntington Beach, Newport Beach, Orange, Anaheim, Tustin, Fullerton, Mission Viejo, Lake Forest, Garden Grove, Santa Ana, Aliso Viejo, Laguna Niguel, Yorba Linda.

Saved-search endpoints:

| Endpoint | Purpose |
|---|---|
| `GET /api/saved-searches` | List saved searches |
| `POST /api/saved-searches` | Create a saved search |
| `PUT /api/saved-searches/{id}` | Update a saved search |
| `DELETE /api/saved-searches/{id}` | Deactivate a saved search |

## Provider Interface

Each adapter exposes:

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

Provider code lives under `app/sources/discovery.py` and is re-exported through `app/discovery/` and `app/discovery/providers/`.

## Approved JSON API Setup

The generic API adapter is optional and never enabled without a configured URL. Use it only for a provider/feed endpoint you are allowed to access.

```bash
export RENTAL_DASHBOARD_PROVIDER_API_URL=https://your-approved-provider.example/listings
export RENTAL_DASHBOARD_PROVIDER_API_KEY=your_optional_key
export RENTAL_DASHBOARD_PROVIDER_API_NAME="Approved Property Feed"
```

Then run:

```bash
curl -X POST http://127.0.0.1:8000/api/discovery/run \
  -H 'content-type: application/json' \
  -d '{"provider_keys":["approved_json_api"],"limit":25}'
```

The endpoint may return a JSON array or an object with `listings`, `results`, or `data`. Tests do not make real external API calls.

## Placeholder Providers

`apify` and `brightdata` are disabled placeholders. They document future integration points for paid/provider-based extraction but intentionally do not call external APIs, use API keys, bypass anti-bot systems, or claim live listing extraction works.

Environment variable placeholders:

```bash
APIFY_API_TOKEN=
BRIGHTDATA_API_KEY=
```

Do not implement either provider without source-specific terms review, a concrete provider contract, and tests.

## Tests

```bash
uv run pytest tests/test_listing_discovery.py tests/test_saved_searches.py
uv run pytest
uv run python -m compileall app
```

The tests cover provider metadata, required adapter interface behavior, mock discovery, run creation/detail, import summaries, saved-search CRUD/defaults, exact URL dedupe, source listing ID dedupe, `last_seen_at` updates, user state preservation, backyard/garage extraction, missing approved API URL handling, and the mock endpoint.
