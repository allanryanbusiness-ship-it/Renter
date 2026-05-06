# Goal: Build the Rental Data Source Strategy and Adapter Layer

You are working in an existing fresh FastAPI project for a Southern California rental property dashboard.

The project already has an initial foundation from the previous goal:
- FastAPI backend
- single-page dark-mode dashboard concept
- separate `index.html`, `app.js`, and `styles.css`
- initial architecture/docs may already exist
- no reliable real data ingestion layer has been completed yet

## Mission

Create the research-backed data source strategy and the first safe ingestion architecture for a rental property comparison dashboard.

The user is looking for rental properties in Orange County, California with:

- 3 bedrooms minimum
- backyard required
- garage required
- strong deal/value potential
- useful comparison across listing sources such as Zillow, Redfin, Realtor, Apartments.com, HotPads, Craigslist, Facebook Marketplace, property management sites, manual entries, CSV exports, and future approved APIs

The project should help aggregate, normalize, compare, rank, and track rental properties.

## Critical Principle

Do not build a brittle scraper that pretends to work.

The goal is to design and implement a durable data ingestion foundation that can support:

1. Manual listing entry
2. CSV import
3. Copy/paste listing import
4. URL metadata capture
5. Future source adapters
6. Optional commercial data providers
7. Optional compliant scraping where allowed
8. Disabled experimental scrapers clearly marked as not production-ready

Do not implement CAPTCHA bypass, stealth bot evasion, deceptive automation, credential abuse, or anything designed to circumvent site protections.

## Deliverables

Create or update the following files.

### 1. `DATA_SOURCES.md`

Write a serious research document covering the real-world options for collecting rental property data.

Include:

- Executive summary
- Recommended MVP source strategy
- Ranking of data source options
- GitHub repo landscape
- Commercial provider landscape
- Manual and semi-manual workflows
- Compliance and reliability risks
- Clear next steps

Research and document the following categories:

#### GitHub / OSS repositories

Find and evaluate repos related to:

- Zillow scraping
- Redfin scraping
- Realtor scraping
- MLS scraping
- multi-site real estate scraping
- rental listing scraping
- property valuation scraping
- Playwright/Puppeteer real estate automation
- Screen shot / OCR / jsonify
- Bright Data real estate scrapers
- ScraperAPI real estate examples
- 2Captcha / CapSolver / Anti-Captcha real estate examples, if they appear in the ecosystem

For each relevant repo, include:

- Name
- URL
- Language
- Sites/sources supported
- What it claims to do
- What seems actually useful
- Risks and brittleness
- Whether we should use it, reference it, or avoid it
- Notes about last activity or maintenance if obvious

Be skeptical. A lot of real estate scraper repos are abandoned, broken, or thin wrappers around paid APIs.

#### Commercial data/provider options

Research and document options such as:

- Bright Data
- Apify
- ScraperAPI
- Oxylabs
- SerpAPI or search-result APIs
- RapidAPI real estate endpoints, if relevant
- Any legitimate real estate/rental APIs that appear useful

For each option, include:

- What data it may provide
- Whether it supports rental listings
- Cost/complexity notes if obvious
- Compliance concerns
- Reliability
- Recommended use case

#### Manual and semi-manual MVP workflows

Document safe workflows such as:

- User manually adds listing details
- User pastes listing text from Zillow/Redfin/Realtor
- User enters listing URL for reference only
- User uploads CSV from an allowed export
- User uses browser bookmarks or clipping flow later
- User stores screenshots or notes manually, if useful
- User tracks changes over time manually until data source adapters mature

### 2. `DATA_SOURCE_MATRIX.md`

Create a practical matrix with these columns:

- Source
- Data Type
- Rental Coverage
- Backyard Detection
- Garage Detection
- Price Reliability
- Freshness
- Automation Difficulty
- Compliance Risk
- Maintenance Risk
- MVP Recommendation
- Future Recommendation

Sources should include at least:

- Manual entry
- Copy/paste import
- CSV import
- Zillow
- Redfin
- Realtor
- Apartments.com
- HotPads
- Craigslist
- Facebook Marketplace
- Property management company sites
- Bright Data
- Apify
- ScraperAPI
- Search APIs
- Public county/city datasets, if useful
- Any relevant GitHub repo category discovered during research

### 3. `SCRAPING_POLICY.md`

Create or update a clear policy for the project.

It should say:

- The app is intended to respect site terms, robots.txt, rate limits, and applicable law.
- The app should not use CAPTCHA bypass, stealth evasion, deceptive browser fingerprints, or credential abuse.
- High-risk scrapers must be disabled by default.
- Manual entry, copy/paste import, CSV import, and approved APIs are preferred.
- Any future scraper must be reviewed per source before activation.
- The app should store provenance metadata for every listing.
- The app should never claim that live Zillow/Redfin scraping works unless it has been implemented, tested, and reviewed.

### 4. Adapter Architecture

Create or update source adapter code.

Suggested files:

- `app/sources/__init__.py`
- `app/sources/base.py`
- `app/sources/manual.py`
- `app/sources/csv_import.py`
- `app/sources/paste_import.py`
- `app/sources/url_reference.py`
- `app/sources/normalizer.py`
- `app/sources/experimental_scraper_placeholder.py`

Implement a clean interface.

The adapter layer should support:

- `source_name`
- `source_type`
- `fetch` or `ingest`
- `normalize`
- `validate`
- provenance metadata
- confidence scoring
- error handling
- disabled-by-default experimental adapters

Do not overengineer it, but make it easy for future agents to add a source adapter without changing the whole app.

### 5. Normalized Listing Schema

Create or update listing schema/model code so every listing can capture:

- id
- title
- description
- address
- city
- county
- state
- zip
- neighborhood
- latitude
- longitude
- price_monthly
- bedrooms
- bathrooms
- square_feet
- lot_size
- property_type
- backyard_status: yes/no/unknown
- backyard_evidence
- garage_status: yes/no/unknown
- garage_evidence
- parking_details
- pet_policy
- laundry
- air_conditioning
- source_name
- source_type
- source_url
- source_listing_id
- source_confidence
- first_seen_at
- last_seen_at
- imported_at
- updated_at
- listing_status
- watchlist_status
- notes
- raw_text
- raw_payload_json
- match_score
- deal_score
- confidence_score

Use the project’s existing patterns. If the previous goal already created models/schemas, extend them carefully instead of replacing everything blindly.

### 6. Copy/Paste Import Feature

Implement a useful MVP-safe copy/paste ingestion endpoint.

Add an endpoint like:

- `POST /api/import/paste`

It should accept:

- raw pasted listing text
- optional source name
- optional source URL
- optional notes

It should attempt to extract obvious fields using deterministic parsing only:

- price
- bedrooms
- bathrooms
- square feet
- city
- state
- garage mentions
- backyard/yard/patio mentions
- pet mentions
- parking mentions

Do not use paid AI APIs.

It is okay if parsing is imperfect. Store the raw text and evidence fields so the user can edit/verify.

### 7. CSV Import Feature

Implement or improve:

- `POST /api/import/csv`

The CSV importer should:

- accept common column names
- map them into normalized listing fields
- preserve unknown columns in raw payload
- return import summary:
  - rows received
  - rows imported
  - rows skipped
  - errors
  - warnings

### 8. URL Reference Feature

Implement:

- `POST /api/listings/url-reference`

This should let the user save a listing URL even if the app cannot scrape the page.

It should store:

- URL
- source name inferred from domain if possible
- title if provided
- notes
- imported_at
- status = needs_manual_review

Do not scrape protected pages here. This is only URL capture/provenance.

### 9. Scoring Updates

Update the scoring logic so it handles confidence and source provenance.

The user’s hard criteria:

- Orange County CA
- 3 bedrooms minimum
- backyard required
- garage required

Score categories:

- hard criteria match
- deal/value score
- confidence score
- data completeness score
- listing freshness score
- source reliability score

Listings with unknown backyard or garage should not be treated the same as confirmed yes or confirmed no. They should be ranked lower than confirmed yes but above confirmed no if the rest of the listing is promising.

### 10. Frontend Updates

Update the single-page dashboard so the user can:

- paste listing text
- upload/import CSV or see clear placeholder if upload is not fully implemented in the frontend
- save a listing URL reference
- see source/provenance badges
- see confidence badges
- see backyard and garage evidence
- filter by:
  - 3+ bedrooms
  - backyard yes/unknown
  - garage yes/unknown
  - city
  - max price
  - source
  - watchlist
- sort by:
  - deal score
  - match score
  - price
  - newest
  - confidence

Keep the UI dark, full-screen, and command-center-like.

### 11. Tests / Validation

Add lightweight tests if the project already has a test setup.

At minimum, add simple validation scripts or test files for:

- paste import parser
- CSV column mapping
- scoring behavior
- source inference from URL

If no test framework exists, create a minimal `tests/` setup with pytest and document how to run it.

### 12. README Update

Update `README.md` with:

- what the app does
- how to run it
- how to use manual entry
- how to use paste import
- how to use CSV import
- how to save URL references
- what data sources are supported today
- what data sources are planned later
- what is intentionally not implemented yet
- known limitations

### 13. AGENTS Update

Update `AGENTS.md` with instructions for future agents:

- Do not implement high-risk scraping without explicit review.
- Prefer adapter-based design.
- Preserve provenance metadata.
- Keep frontend as separate HTML/CSS/JS unless explicitly changed.
- Add tests for import/scoring changes.
- Do not claim live scraping works unless verified.
- Keep docs updated when adding a source.

## Implementation Rules

- Inspect existing files first.
- Preserve good work from the previous goal.
- Extend existing architecture instead of rewriting unnecessarily.
- Keep the app runnable.
- Do not introduce heavy dependencies unless justified.
- Prefer standard library parsing for paste import.
- Use clear error messages.
- Avoid fake functionality.
- If something is a placeholder, label it clearly as a placeholder.
- Do not use external paid APIs.
- Do not require API keys for the MVP.
- Do not break existing dashboard behavior.

## Completion Audit

Before marking the goal complete, produce a final audit with:

| Requirement | Status | Notes |
|---|---|---|
| DATA_SOURCES.md created/updated | pass/partial/fail | ... |
| DATA_SOURCE_MATRIX.md created | pass/partial/fail | ... |
| SCRAPING_POLICY.md created/updated | pass/partial/fail | ... |
| Adapter layer implemented | pass/partial/fail | ... |
| Paste import endpoint works | pass/partial/fail | ... |
| CSV import endpoint works | pass/partial/fail | ... |
| URL reference endpoint works | pass/partial/fail | ... |
| Scoring updated | pass/partial/fail | ... |
| Frontend updated | pass/partial/fail | ... |
| Tests or validation added | pass/partial/fail | ... |
| README updated | pass/partial/fail | ... |
| AGENTS.md updated | pass/partial/fail | ... |
| App still runs | pass/partial/fail | ... |

## Final Response

When complete, summarize:

1. What changed
2. How to run it
3. Which files matter most
4. What is still intentionally not implemented
5. The best next `/goal` to run
