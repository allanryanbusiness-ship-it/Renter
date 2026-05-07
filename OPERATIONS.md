# Operations

This app is designed for local daily use. Keep it boring: one SQLite database, explicit backups, portable JSON/CSV exports, and non-destructive restore.

## Daily Start

```bash
uv sync
uv run python run_local.py
```

Or:

```bash
./start.sh
```

Windows:

```bat
start.bat
```

The run script prints:

- Dashboard URL
- SQLite database path
- Backup folder
- Log folder

Default dashboard: `http://127.0.0.1:8000`

## File Locations

Default paths:

- Database: `data/renter.db`
- Backups: `backups/`
- Logs: `logs/renter.log`
- Exports: browser/downloaded from API endpoints

Environment overrides:

```bash
export RENTAL_DASHBOARD_DB_PATH=/absolute/path/renter.db
export RENTAL_DASHBOARD_BACKUP_DIR=/absolute/path/backups
export RENTAL_DASHBOARD_LOG_DIR=/absolute/path/logs
export RENTAL_DASHBOARD_HOST=127.0.0.1
export RENTAL_DASHBOARD_PORT=8000
export RENTAL_DASHBOARD_APPROVED_FEED_PATH=/absolute/path/approved_provider_feed.json
```

Use absolute paths for long-lived daily data. Relative paths work, but absolute paths reduce confusion.

## Automatic Discovery Workflow

From the dashboard:

1. Open `Automatic Discovery`.
2. Leave `Approved Demo Provider Feed` selected, or select a configured provider API.
3. Use `Dry run only` if you want to preview candidates without importing.
4. Click `Run Discovery`.
5. Review imported listings, possible duplicate warnings, and score explanations in the deal queue.

From the API:

```bash
curl -X POST http://127.0.0.1:8000/api/discovery/run \
  -H 'content-type: application/json' \
  -d '{"provider_keys":["approved_demo_feed"],"limit":25}'
```

RentCast requires `RENTAL_DASHBOARD_RENTCAST_ENABLED=true` and `RENTAL_DASHBOARD_RENTCAST_API_KEY`. See [AUTOMATIC_LISTING_DISCOVERY.md](AUTOMATIC_LISTING_DISCOVERY.md).

## Backup Workflow

From the dashboard:

1. Open the `System` panel.
2. Click `Create Backup`.
3. Confirm the backup path shown in the status message.

From the API:

```bash
curl -X POST http://127.0.0.1:8000/api/admin/backup
```

Backups are timestamped SQLite copies under `backups/` and are never overwritten silently.

## Export Workflow

Dashboard buttons:

- `Export JSON`: listing-focused JSON
- `Export CSV`: spreadsheet-friendly listing export
- `Full Export`: listings, scores, sources, search criteria, and benchmark data

API:

```bash
curl http://127.0.0.1:8000/api/export/listings.json -o renter_listings.json
curl http://127.0.0.1:8000/api/export/listings.csv -o renter_listings.csv
curl http://127.0.0.1:8000/api/export/full.json -o renter_full.json
```

Use `Full Export` before major changes.

## Restore / Import Workflow

The restore endpoint is merge-only. It does not wipe the current database.

Dashboard:

1. Open `System`.
2. Paste a prior full export JSON payload.
3. Click `Import Full JSON`.
4. Review imported, updated, skipped, and error counts.

API:

```bash
curl -X POST http://127.0.0.1:8000/api/import/full-json \
  -H 'content-type: application/json' \
  --data-binary @renter_full.json
```

Duplicate behavior:

- Exact source URL updates the existing listing.
- Notes are merged without duplicating identical note text.
- Imports are non-destructive by default.

## Data Quality Workflow

Dashboard:

- The `System` panel shows listing count, last backup, benchmark review date, unknown backyard/garage counts, duplicate groups, and warnings.

API:

```bash
curl http://127.0.0.1:8000/api/admin/data-quality
curl http://127.0.0.1:8000/api/admin/status
```

Review data quality before contacting property managers.

## Benchmark Updates

Benchmark assumptions live in:

```text
app/data/city_benchmarks.json
```

After editing:

```bash
uv run pytest tests/test_benchmarks.py tests/test_deal_score_calibration.py tests/test_scoring.py
```

Also update [MARKET_RESEARCH.md](MARKET_RESEARCH.md) if values or sources change.

## Safe Shutdown

Use `Ctrl+C` in the terminal running the app. SQLite commits happen during API requests; shutting down the server does not reset data.

## Docker

Docker support is intentionally skipped for this local-first reliability pass. The recommended daily path is `uv run python run_local.py` with `RENTAL_DASHBOARD_DB_PATH` pointing at a stable local file. Add Docker later only if deployment or cross-machine packaging becomes a requirement.

## Troubleshooting

If the dashboard starts with only demo listings, check `RENTAL_DASHBOARD_DB_PATH`. You may be pointing at a different database file.

If backups fail, check that the backup directory exists and is writable.

If a restore import skips records, inspect the returned `errors` list. Each listing needs at least title, city, and price.

If scores look stale, restart the app or update search criteria to trigger rescoring.
