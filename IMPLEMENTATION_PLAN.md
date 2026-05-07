# Implementation Plan

## Phase 1

1. Establish a canonical listing schema, source model, search criteria model, score model, notes model, watchlist model, and import-run model.
2. Deliver a FastAPI app that serves both JSON APIs and a single dark dashboard page.
3. Seed Orange County demo listings so the app is usable immediately.
4. Build manual-entry ingestion for blocked or unavailable listings.
5. Keep adapter interfaces pluggable while leaving risky scrapers disabled by default.

## Phase 2

1. Add CSV import and export workflows.
2. Add source-run history screens and watchlist workflows.
3. Add approved/provider-based automatic discovery with local feed and optional provider API adapters.
4. Add auth, saved views, alerts, and scheduled refresh jobs.
