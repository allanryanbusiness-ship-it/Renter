# AGENTS

## Purpose

This repository is for a Southern California rental comparison dashboard focused on Orange County, California.

## Commands

```bash
uv sync
uv run python run_local.py --check
uv run python run_local.py
uv run python -m app.main
uv run python -m compileall app
uv run pytest
```

## Repo Rules

- Keep data-source integrations compliant with site terms, robots policies, and rate limits.
- Do not add CAPTCHA bypass, stealth scraping, proxy-rotation evasion, or deceptive automation.
- Prefer licensed APIs, public data, feed partnerships, CSV imports, and manual entry.
- Never add destructive data resets, database deletes, or overwrite-style restores without explicit user approval.
- Preserve backward compatibility of JSON/CSV exports when practical.
- Keep backup, export, full JSON import, and data-quality workflows working when changing models.
- Add migration notes and tests when schema changes affect existing SQLite databases.
- Do not log sensitive raw clipped text, private notes, phone numbers, or email bodies unnecessarily.
- Keep local-first persistence reliable and avoid creating databases in random working directories.
- Preserve the browser clipper as a user-driven capture workflow; it must not become background scraping.
- Preserve the adapter boundary between ingestion and the core app.
- Automatic discovery must use approved local feeds or configured provider APIs only.
- Do not implement high-risk scraping without explicit source review.
- Preserve provenance metadata for every imported listing.
- Do not commit API keys or expose provider secrets in frontend code.
- Keep real providers disabled or skipped when required configuration is missing.
- Add tests for every provider adapter, including missing-key behavior.
- Preserve `source_listing_id`, `discovery_run_id`, raw payload, first/last seen timestamps, and provenance notes on discovery imports.
- Preserve `source_domain`, `source_name`, `source_url`, and `source_type` for browser clips and URL references.
- Sanitize clipped text before storage or display; never execute clipped HTML or script.
- Do not fetch source listing URLs server-side from the browser clip endpoint.
- Keep scoring explainable in backend code and API responses; do not hide score logic in frontend-only code.
- Preserve backyard/garage evidence snippets and raw imported text.
- Preserve older notes, decision state, watchlist state, and private notes when exact source URL or source listing ID duplicate imports update a listing.
- Do not claim placeholder benchmark data is real market data.
- Benchmark data must include provenance: source name, URL, accessed date, confidence, and notes.
- Do not fabricate precise market data. If exact 3-bedroom city data is unavailable, mark estimates as low confidence or fallback.
- Do not add scraping, CAPTCHA bypass, or anti-bot evasion to collect benchmark data.
- Keep benchmark logic explainable in score reasons, warnings, and API fields.
- Add tests when changing scoring, parser behavior, duplicate detection, clipped import behavior, decision workflow, or source behavior.
- Add or update `tests/test_listing_discovery.py` and `tests/test_saved_searches.py` when changing discovery providers, dedupe behavior, provider filtering, run history, or saved searches.
- Keep the frontend as separate `templates/index.html`, `static/js/app.js`, and `static/css/styles.css` unless explicitly changed.
- Add or update tests for import parsing, CSV mapping, source inference, and scoring changes.
- Do not claim live Zillow, Redfin, Realtor.com, Apartments.com, HotPads, Craigslist, or Facebook Marketplace scraping works unless it has been implemented, tested, reviewed, and documented.
- Update `DATA_SOURCES.md`, `DATA_SOURCE_MATRIX.md`, and `SCRAPING_POLICY.md` whenever adding or changing a source path.

## Architecture Pointers

- `app/adapters/` contains source interfaces and disabled high-risk stubs.
- `app/sources/` contains the current safe ingestion adapter layer.
- `app/sources/discovery.py` contains automatic discovery provider adapters.
- `app/discovery/` is the automatic discovery package boundary and owns persisted discovery provider/run audit helpers.
- `app/services/discovery.py` orchestrates provider discovery runs.
- `app/services/saved_searches.py` owns saved discovery/search criteria.
- `app/normalization/` converts incoming data into the canonical listing model.
- `app/services/scoring.py` owns ranking logic.
- `app/services/benchmark_service.py` loads, validates, normalizes, and returns editable city benchmark data.
- `app/services/reliability.py` owns backup, export, merge-import, status, and data-quality services.
- `app/data/city_benchmarks.json` contains editable sourced benchmark estimates for deal scoring; these are not authoritative and must stay labeled by confidence.
- `MARKET_RESEARCH.md` documents benchmark source notes, confidence, and limitations.
- `app/api/routes.py` exposes the dashboard API surface.
- `static/js/bookmarklet.js` is the source of truth for the browser clipper bookmarklet shown in the dashboard.
- `run_local.py`, `start.sh`, and `start.bat` are the user-facing local run entrypoints.
- `OPERATIONS.md` documents daily use, backup, restore, and data-quality workflows.
