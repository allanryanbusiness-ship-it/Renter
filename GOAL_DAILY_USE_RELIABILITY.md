# Goal: Make the Rental Dashboard Reliable for Daily Local Use

You are working in an existing FastAPI rental property dashboard project.

The project already has:
- FastAPI backend
- separate frontend files:
  - templates/index.html
  - static/js/app.js
  - static/css/styles.css
- dark-mode single-page dashboard
- normalized listing schema
- safe ingestion architecture
- manual listing entry
- paste import
- CSV import
- URL reference support
- browser clipping/bookmarklet workflow
- scoring system
- score breakdowns
- decision workflow
- needs-review logic
- source/provenance tracking
- Orange County rental benchmark calibration
- editable city benchmark data

## Mission

Make the app reliable enough for daily use as a local rental-hunting command center.

The user is searching for Orange County, California rental properties with:

- 3 bedrooms minimum
- backyard required
- garage required
- strong value/deal potential
- fast browser clipping
- accurate comparison
- safe data capture
- reliable local persistence

The app should now feel like something the user can actually run every day without worrying about losing listings, notes, scores, clipped data, or decision history.

---

# 1. Local Persistence Hardening

Audit and improve how the app stores data.

Requirements:

- SQLite database should use a stable configurable path.
- Avoid accidentally creating multiple databases in random working directories.
- Add a clear default location.
- Add environment variable override such as `RENTAL_DASHBOARD_DB_PATH`.
- Ensure app startup creates needed folders.
- Ensure migrations or schema initialization are safe and repeatable.
- Avoid destructive resets unless explicitly requested.
- Add clear logging when database is initialized.

If the app already has a database setup, extend it carefully.

---

# 2. Backup System

Add a simple backup workflow.

Create backend utility and/or CLI script such as:

- `scripts/backup_db.py`
- `app/services/backup_service.py`

Requirements:

- Create timestamped SQLite backup files.
- Store backups in a clear folder such as `backups/`.
- Do not overwrite old backups.
- Include metadata file if useful.
- Add endpoint or local script for manual backup.

Possible endpoint:

- `POST /api/admin/backup`

Response should include:

```json
{
  "data": {
    "backup_path": "backups/rental_dashboard_2026-05-06_120000.sqlite",
    "created_at": "2026-05-06T12:00:00Z"
  },
  "errors": []
}
```

If exposing admin endpoint feels risky, keep it local-script only and document it.

---

# 3. Export System

Add data export so the user is never locked in.

Implement exports for:

- JSON
- CSV

Suggested endpoints:

- `GET /api/export/listings.json`
- `GET /api/export/listings.csv`
- `GET /api/export/full.json`

Exports should include:

- listings
- scores
- score breakdowns if stored or recomputable
- decision status
- notes
- source provenance
- benchmark context where practical
- imported/clipped raw text where safe

Also add a frontend button or panel:

- Export JSON
- Export CSV
- Full backup/export instructions

---

# 4. Import System for Restoring Data

Add or improve data import.

Suggested endpoint:

- `POST /api/import/full-json`

Requirements:

- Accept prior exported JSON.
- Validate shape.
- Avoid duplicate listings where possible.
- Preserve notes and decision statuses.
- Return clear import summary:
  - records received
  - records imported
  - records updated
  - records skipped
  - errors
  - warnings

Do not make this destructive by default.

If full restore is too risky, implement safe import-only merge and document limitations.

---

# 5. Run Scripts

Add simple run scripts for the user.

Create:

- `run_local.py` or `scripts/run_local.py`
- `start.bat` for Windows if practical
- `start.sh` for macOS/Linux if practical

Requirements:

- Start FastAPI with the right host/port.
- Use stable DB path.
- Print dashboard URL.
- Print database path.
- Print backup folder path.
- Avoid requiring the user to remember a long uvicorn command.

Example behavior:

```bash
python run_local.py
```

Should print something like:

```text
Rental Dashboard starting...
Dashboard: http://127.0.0.1:8000
Database: data/rental_dashboard.sqlite
Backups: backups/
```

---

# 6. Logging and Error Handling

Improve observability.

Requirements:

- Add structured-ish logs for:
  - app startup
  - database path
  - imports
  - browser clips
  - scoring recalculation
  - exports
  - backups
  - errors
- Avoid logging sensitive raw listing text unnecessarily.
- Show user-friendly frontend errors.
- API errors should be consistent.
- Add clear validation errors for bad imports.

Create logs folder if appropriate:

- `logs/`

Or use standard output only if simpler.

---

# 7. Frontend Reliability Panel

Add a simple “System” or “Data” panel to the dashboard.

It should show:

- database status if available
- number of listings
- last backup time if available
- export buttons
- backup button if endpoint is implemented
- import JSON restore area if implemented
- app version if available
- warnings if benchmark data is old or missing

Keep it clean and dark-mode consistent.

---

# 8. Data Quality Checks

Add a simple data quality audit.

Create endpoint:

- `GET /api/admin/data-quality`

Or service function used by frontend.

It should report:

- listings missing price
- listings missing city
- listings missing source URL
- listings with unknown backyard
- listings with unknown garage
- listings missing score breakdown
- potential duplicates
- old benchmark data
- listings needing review

Show this in the dashboard if practical.

---

# 9. Optional Docker Support

Add Docker only if it is straightforward and does not destabilize the app.

Possible files:

- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore`

Requirements if implemented:

- Persist SQLite database via volume.
- Expose app on port 8000.
- Document backup/export with Docker.

If Docker adds too much risk or time, skip it and explicitly document that local Python run is the recommended path.

---

# 10. Tests and Validation

Add or update tests for:

- database path configuration
- backup creation
- JSON export
- CSV export
- full JSON import/merge behavior
- duplicate handling during restore
- data quality endpoint/service
- frontend-independent API behavior
- app startup import checks

Suggested files:

- `tests/test_backup.py`
- `tests/test_exports.py`
- `tests/test_full_import.py`
- `tests/test_data_quality.py`
- update existing API tests if present

Run:

```bash
pytest
```

Also run:

```bash
python -m compileall app
```

If run scripts exist, smoke test at least one:

```bash
python run_local.py
```

If the smoke test cannot be run because it blocks the terminal, document how it was validated.

---

# 11. Documentation Updates

Update:

- `README.md`
- `AGENTS.md`
- optional `OPERATIONS.md`

## README.md should include:

- quick start
- run command
- dashboard URL
- database location
- how to set custom database path
- how to back up data
- how to export JSON/CSV
- how to restore/import JSON
- how to use browser clipper
- how to troubleshoot common issues
- current limitations

## OPERATIONS.md should include if created:

- daily use checklist
- backup workflow
- restore workflow
- data quality workflow
- updating benchmark data
- safe shutdown notes
- where files are stored

## AGENTS.md should tell future agents:

- never add destructive data resets without explicit user approval
- preserve backward compatibility of exports when practical
- add migration notes when schema changes
- keep backup/export working
- do not log sensitive raw clipped text unnecessarily
- keep data source provenance intact
- keep local-first design reliable

---

# 12. Implementation Rules

- Preserve previous work.
- Keep the app runnable.
- Do not break dashboard, scoring, clipping, imports, or decision workflow.
- Do not implement risky scraping.
- Do not add paid APIs.
- Do not require API keys.
- Do not make destructive imports or resets the default.
- Do not silently overwrite backups.
- Keep frontend vanilla JS/CSS/HTML.
- Keep dependency footprint reasonable.
- Prefer simple, boring reliability over complex architecture.
- Make errors clear and recoverable.
- Make data portable.

---

# 13. Completion Audit

Before finishing, perform a final audit.

Use this table:

| Requirement | Status | Notes |
|---|---|---|
| Stable DB path configured | pass/partial/fail | ... |
| Backup workflow added | pass/partial/fail | ... |
| JSON export added | pass/partial/fail | ... |
| CSV export added | pass/partial/fail | ... |
| Full JSON import/merge added | pass/partial/fail | ... |
| Run script added | pass/partial/fail | ... |
| Logging improved | pass/partial/fail | ... |
| Frontend data/system panel added | pass/partial/fail | ... |
| Data quality checks added | pass/partial/fail | ... |
| Docker support added or intentionally skipped | pass/partial/fail | ... |
| Tests added/updated | pass/partial/fail | ... |
| README updated | pass/partial/fail | ... |
| AGENTS.md updated | pass/partial/fail | ... |
| App still runs | pass/partial/fail | ... |

---

# 14. Final Response

When complete, summarize:

1. What changed
2. How to run the app
3. Where the database lives
4. How to back up data
5. How to export data
6. How to restore/import data
7. Tests run and results
8. Known limitations
9. The best next `/goal` to run

Also include:

- any manual setup needed
- any skipped reliability items and why
- biggest remaining product risk
- highest-leverage next improvement

---

# 15. Recommended Next Goal After This

After this goal, recommend exactly one next goal.

Choose from:

## Option A: Saved Searches and Alerts

Best if the app needs to become an active rental-hunting assistant.

Goal:
- Add saved searches.
- Add check reminders.
- Add watchlist alerts based on imported/clipped data.
- Add “contact today” queue.
- Add next-action reminders.
- Add stale listing warnings.
- Add daily review mode.

## Option B: Property Visit and Decision Toolkit

Best if the user is actively contacting and touring rentals.

Goal:
- Add tour checklist.
- Add landlord/property manager contact tracker.
- Add deal memo export.
- Add pros/cons comparison.
- Add final decision scorecard.
- Add application readiness tracker.

## Option C: Deployment

Best if the app should run somewhere other than the local machine.

Goal:
- Prepare deployment for Railway/VPS.
- Add production settings.
- Add persistent storage notes.
- Add security review.
- Add environment configuration.
- Add reverse proxy notes if needed.

End by recommending exactly one next goal and explain why.
