# Automatic Listing Discovery Audit

Audit date: 2026-05-07

## Scope Note

`GOAL_AUTOMATIC_LISTING_DISCOVERY.md` was fetched from `https://github.com/allanryanbusiness-ship-it/Renter` after the user clarified that the file had to come from the GitHub repo. This audit is against that fetched goal file and the actual local repository files.

## Completion Audit

| Requirement | Status | Notes |
|---|---|---|
| Discovery architecture added | pass | `app/discovery/`, `app/discovery/base.py`, `app/discovery/service.py`, `app/discovery/models.py`, `app/discovery/providers/`, `app/services/discovery.py`, and `app/services/saved_searches.py` define package boundaries |
| Provider interface added | pass | `DiscoveryProviderAdapter` and concrete adapters expose provider name/type, enabled/config state, filters, search, normalize, validation, rate-limit notes, and compliance notes |
| RentCast or chosen API provider adapter added | pass | `RentCastRentalListingsAdapter` supports city/ZIP query construction and is disabled unless configured |
| Missing API key handled gracefully | pass | RentCast returns `not_configured` provider metadata and discovery runs are recorded as skipped without network calls |
| Mock discovery provider works | pass | `mock` provider imports local Orange County demo candidates without credentials and is available through the dashboard/API |
| Discovery run model added | pass | `DiscoveryRun` tracks provider, criteria snapshot, dry/import mode, counts, warnings, errors, candidate preview, and listing IDs |
| Discovery endpoints added | pass | `GET /api/discovery/providers`, `POST /api/discovery/run`, `GET /api/discovery/runs`, and `GET /api/discovery/runs/{id}` |
| Saved searches added | pass | `GET/POST/PUT/DELETE /api/saved-searches` manage saved criteria backed by `SearchCriteria` |
| Default Orange County saved search added | pass | Startup ensures `Orange County 3BR Yard + Garage` with the required Orange County city list and 3BR yard/garage constraints |
| Deduplication improved | pass | Exact URL and source listing ID update existing listings; possible duplicates are flagged by address, address + price, or title + city + price |
| Backyard/garage extraction applied to discovered listings | pass | Provider normalization parses explicit fields plus description/parking/raw text and imports weak evidence as review-needed |
| Dashboard discovery UI added | pass | Automatic Discovery panel includes provider status cards, saved-search selector, Run Discovery, Mock Discovery, warnings, run history, counts, and discovery filters |
| Provider config docs added | pass | `README.md`, `DISCOVERY.md`, `AUTOMATIC_LISTING_DISCOVERY.md`, `.env.example`, `DATA_SOURCES.md`, and `SCRAPING_POLICY.md` document RentCast and placeholder env vars |
| Tests added/updated | pass | `tests/test_listing_discovery.py` and `tests/test_saved_searches.py` cover provider interface, mock discovery, runs, saved searches, dedupe, missing keys, and extraction |
| README updated | pass | README documents discovery providers, mock discovery, RentCast setup, saved-search endpoints, dedupe, inference, and unsupported scraping claims |

## Additional Evidence

| Area | Status | Evidence |
|---|---|---|
| Provider placeholders | pass | `app/discovery/providers/apify_placeholder.py` and `brightdata_placeholder.py` re-export disabled placeholder adapters |
| Imported listing provenance | pass | `Listing.discovery_run_id` and `raw_payload["discovery_run_id"]` are set after import runs |
| User state preservation | pass | Exact duplicate updates do not overwrite decision status, watchlist status, private notes, or existing notes |
| Full export compatibility | pass | `/api/export/full.json` includes discovery providers/runs and listing `discovery_run_id` |
| No stealth scraping | pass | No CAPTCHA bypass, proxy rotation, browser fingerprinting, credential abuse, or listing-page crawler was added |

## Files Added

- `DISCOVERY.md`
- `GOAL_AUTOMATIC_LISTING_DISCOVERY.md`
- `app/discovery/base.py`
- `app/discovery/models.py`
- `app/discovery/providers/__init__.py`
- `app/discovery/providers/apify_placeholder.py`
- `app/discovery/providers/brightdata_placeholder.py`
- `app/discovery/providers/mock_provider.py`
- `app/discovery/providers/rentcast.py`
- `app/discovery/service.py`
- `app/services/deduplication_service.py`
- `app/services/discovery_run_service.py`
- `app/services/saved_searches.py`
- `tests/test_saved_searches.py`

## Files Updated

- `.env.example`
- `AGENTS.md`
- `ARCHITECTURE.md`
- `AUTOMATIC_LISTING_DISCOVERY.md`
- `DATA_SOURCES.md`
- `README.md`
- `SCRAPING_POLICY.md`
- `app/api/routes.py`
- `app/config.py`
- `app/db.py`
- `app/discovery/__init__.py`
- `app/discovery/adapters.py`
- `app/discovery/persistence.py`
- `app/main.py`
- `app/models.py`
- `app/schemas.py`
- `app/seed.py`
- `app/services/discovery.py`
- `app/services/listings.py`
- `app/services/reliability.py`
- `app/sources/discovery.py`
- `static/css/styles.css`
- `static/js/app.js`
- `templates/index.html`
- `tests/test_listing_discovery.py`

## Verification Commands

```bash
uv run pytest tests/test_listing_discovery.py -q
uv run pytest tests/test_saved_searches.py -q
uv run pytest -q
uv run python -m compileall app
node --check static/js/app.js
git diff --check
```

## Verification Results

- `uv run pytest tests/test_listing_discovery.py -q`: 10 passed.
- `uv run pytest tests/test_saved_searches.py -q`: 2 passed.
- `uv run pytest -q`: 47 passed.
- `uv run python -m compileall app`: passed.
- `node --check static/js/app.js`: passed.
- `uv run python run_local.py --check`: passed and resolved database/backup/log paths.
- `git diff --check`: passed.

## Live Smoke Results

- Restarted the local server on `http://127.0.0.1:8000`.
- `GET /`: returned HTTP 200.
- `GET /api/discovery/providers`: returned `mock`, `approved_demo_feed`, `rentcast`, `apify`, and `brightdata` with correct configured/placeholder states.
- `GET /api/saved-searches`: returned `Orange County 3BR Yard + Garage` with the required city list.
- `POST /api/discovery/run` with `{"provider_keys":["mock"],"limit":2,"dry_run":true,"import_results":false}`: created dry-run `discovery_run_id=3` with 2 candidate previews.
- `GET /api/discovery/runs/3`: returned the criteria snapshot and candidate preview.
- `POST /api/discovery/run` with `{"provider_keys":["mock"],"limit":2,"dry_run":false,"import_results":true}`: completed import/update run `discovery_run_id=4`, updated 2 existing listings, and returned listing IDs `[9, 10]`.
- `GET /api/listings?discovery_only=true`: returned 2 listings linked to `discovery_run_id=4`.
- `GET /api/export/full.json`: returned 5 discovery providers, 4 discovery runs, and listings with `discovery_run_id`.
- Final current-code smoke after restart: `POST /api/discovery/run` with `{"provider_keys":["mock"],"limit":1,"dry_run":false,"import_results":true}` completed run `discovery_run_id=5`, updated 1 listing, and the immediate API response included `discovery_run_id=5` in both the listing field and raw payload.

Smoke commands used:

```bash
curl http://127.0.0.1:8000/
curl http://127.0.0.1:8000/api/discovery/providers
curl http://127.0.0.1:8000/api/saved-searches
curl -X POST http://127.0.0.1:8000/api/discovery/run \
  -H 'content-type: application/json' \
  -d '{"provider_keys":["mock"],"limit":2,"dry_run":true,"import_results":false}'
curl -X POST http://127.0.0.1:8000/api/discovery/run \
  -H 'content-type: application/json' \
  -d '{"provider_keys":["mock"],"limit":2,"dry_run":false,"import_results":true}'
curl 'http://127.0.0.1:8000/api/listings?discovery_only=true'
curl http://127.0.0.1:8000/api/export/full.json
```

## Residual Risks

- RentCast calls require a real account/key to verify against the live provider API.
- Mock and approved local feed data are demo data, not live market coverage.
- Apify and Bright Data are placeholders only and must not be treated as implemented.
- Existing code still emits `datetime.utcnow()` deprecation warnings under Python 3.13.

## Conclusion

Automatic discovery is implemented as working application code, not markdown-only documentation. Mock discovery works without credentials, the real provider path is present but safely disabled when unconfigured, candidates import into the existing scoring/review workflow, dedupe preserves user state, and the repository has tests and documentation for the compliant provider-based strategy.
