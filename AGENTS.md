# AGENTS

## Purpose

This repository is for a Southern California rental comparison dashboard focused on Orange County, California.

## Commands

```bash
uv sync
uv run python -m app.main
uv run python -m compileall app
```

## Repo Rules

- Keep data-source integrations compliant with site terms, robots policies, and rate limits.
- Do not add CAPTCHA bypass, stealth scraping, proxy-rotation evasion, or deceptive automation.
- Prefer licensed APIs, public data, feed partnerships, CSV imports, and manual entry.
- Preserve the adapter boundary between ingestion and the core app.

## Architecture Pointers

- `app/adapters/` contains source interfaces and disabled high-risk stubs.
- `app/normalization/` converts incoming data into the canonical listing model.
- `app/services/scoring.py` owns ranking logic.
- `app/api/routes.py` exposes the dashboard API surface.

