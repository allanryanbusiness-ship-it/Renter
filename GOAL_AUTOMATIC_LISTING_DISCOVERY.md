# Goal: Build Automatic Rental Listing Discovery

You are working in an existing FastAPI rental property dashboard project.

The project already has:
- FastAPI backend
- separate frontend files:
  - templates/index.html
  - static/js/app.js
  - static/css/styles.css
- dark-mode single-page dashboard
- normalized listing schema
- manual entry
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
- backup/export/local reliability work may exist

## Mission

Add an automatic listing discovery layer so the user does not have to manually check Zillow, Redfin, Realtor, Apartments.com, HotPads, Craigslist, Facebook Marketplace, and property management sites one by one.

The user is searching for Orange County, California rental properties with:
- 3 bedrooms minimum
- backyard required or likely
- garage required or likely
- strong value/deal potential
- active rental status
- source URL preserved
- score/rank/review workflow

The product should become:

> Set search criteria once, run discovery, import candidate listings, deduplicate, score, and review only the best matches.

## Core Principle

Use approved/provider-based or compliant data sources first.

Do not implement CAPTCHA bypass, stealth scraping, proxy evasion, browser fingerprint evasion, credential abuse, or deceptive automation.

Do not claim Zillow/Redfin/Realtor scraping works unless an adapter is actually implemented, tested, and clearly documented.

The first production-ready automatic discovery path should prefer a documented API/provider.

---

# 1. Discovery Architecture

Create or update a discovery architecture that separates:

- saved search criteria
- provider adapters
- discovery runs
- raw provider payloads
- normalization
- deduplication
- scoring
- review queue

Suggested files:

- `app/discovery/__init__.py`
- `app/discovery/base.py`
- `app/discovery/service.py`
- `app/discovery/models.py` if appropriate
- `app/discovery/providers/rentcast.py`
- `app/discovery/providers/apify_placeholder.py`
- `app/discovery/providers/brightdata_placeholder.py`
- `app/discovery/providers/mock_provider.py`
- `app/services/deduplication_service.py`
- `app/services/discovery_run_service.py`

Keep the design simple and practical.

---

# 2. Provider Adapter Interface

Define a provider adapter interface.

Each provider should support:

- provider_name
- provider_type
- is_enabled
- requires_api_key
- supported_locations
- supports_rentals
- supports_filters
- search(criteria)
- normalize(raw_listing)
- validate_config()
- rate_limit_notes
- compliance_notes

The provider adapter should return normalized candidate listings in the app’s existing schema.

Every imported listing must preserve:

- source_name
- source_type
- source_url
- source_listing_id if available
- raw_payload_json
- imported_at
- first_seen_at
- last_seen_at
- discovery_run_id
- provenance notes

---

# 3. RentCast Provider Adapter

Implement a first real provider adapter for RentCast or another documented rental listing API if the repo already chose one.

Use environment variable configuration:

- `RENTCAST_API_KEY`

If no API key is present:
- provider should be disabled gracefully
- app should explain how to configure it
- tests should use mocks, not real API calls

The adapter should support searching by:
- city and state
- zip code if available
- radius if implemented later

Default Orange County city search list:
- Irvine
- Costa Mesa
- Huntington Beach
- Newport Beach
- Orange
- Anaheim
- Tustin
- Fullerton
- Mission Viejo
- Lake Forest
- Garden Grove
- Santa Ana
- Aliso Viejo
- Laguna Niguel
- Yorba Linda

Default search constraints:
- state = CA
- status = active if provider supports it
- property type = rental if provider supports it
- min bedrooms = 3 if provider supports it
- otherwise filter after import

Do not hardcode the API key.

Do not fail app startup if the key is missing.

---

# 4. Mock Discovery Provider

Add a mock provider that simulates automatic discovery without external API keys.

This is important so the feature can be tested and demoed immediately.

The mock provider should return realistic Orange County rental listings with:
- source URLs
- prices
- beds
- baths
- sqft
- city
- description
- backyard clues
- garage clues
- property type
- active status

The mock provider should be clearly labeled as demo/mock data.

---

# 5. Discovery Run Model

Add a discovery run concept.

Each run should track:

- id
- provider_name
- search_name
- search_criteria
- started_at
- finished_at
- status
- raw_count
- imported_count
- updated_count
- duplicate_count
- skipped_count
- error_count
- warnings
- errors

Add endpoints:

- `POST /api/discovery/run`
- `GET /api/discovery/runs`
- `GET /api/discovery/runs/{id}`
- `GET /api/discovery/providers`

Optional:
- `POST /api/discovery/run/mock`
- or allow provider = mock

---

# 6. Saved Search Criteria

Add saved search support if it does not already exist.

A saved search should include:

- name
- county
- state
- cities
- zip_codes
- min_bedrooms
- max_price
- backyard_required
- garage_required
- allow_unknown_backyard
- allow_unknown_garage
- property_types
- provider_names
- is_active
- created_at
- updated_at

Add endpoints:

- `GET /api/saved-searches`
- `POST /api/saved-searches`
- `PUT /api/saved-searches/{id}`
- `DELETE /api/saved-searches/{id}`

Default saved search:

- name: Orange County 3BR Yard + Garage
- county: Orange County
- state: CA
- cities: the Orange County city list above
- min_bedrooms: 3
- backyard_required: true
- garage_required: true
- allow_unknown_backyard: true
- allow_unknown_garage: true

---

# 7. Deduplication

Improve deduplication for automatically discovered listings.

Deduplicate using:
- exact source URL
- source listing ID
- normalized address
- title + city + price
- address + price
- fuzzy warning only if uncertain

Behavior:
- exact duplicate should update existing listing
- possible duplicate should import but mark `needs_review`
- preserve user notes, decision status, watchlist, and private notes
- update last_seen_at when rediscovered
- preserve first_seen_at from original listing

Add clear import summary.

---

# 8. Attribute Extraction for Backyard and Garage

Many APIs may not provide explicit backyard/garage fields.

Use existing deterministic parser on:
- description
- amenities
- features
- raw text
- provider payload fields

Extract:
- backyard_status
- backyard_evidence
- garage_status
- garage_evidence
- parking_details

Do not overstate certainty.
If evidence is weak:
- mark unknown
- add needs-review badge
- add next action: verify backyard or verify garage

---

# 9. Dashboard Discovery UI

Add a dashboard section called:

- Automatic Discovery
- Find Listings
- Listing Discovery
- Search Runs

It should include:

- provider status cards
- saved search selector
- Run Discovery button
- Mock Discovery button if real provider not configured
- API key missing warning if applicable
- latest discovery run summary
- import counts
- duplicate counts
- error/warning display
- link/filter to newly discovered listings
- filter for “new from discovery”
- filter for “needs review from discovery”

Keep the UI dark, single-page, and vanilla JS/CSS/HTML.

---

# 10. Provider Configuration UI or Docs

At minimum, document how to configure provider API keys.

Optional simple UI:
- show configured/not configured status
- do not display API key value
- explain required environment variables

Document:
- `RENTCAST_API_KEY`
- optional future `APIFY_API_TOKEN`
- optional future `BRIGHTDATA_API_KEY`

Do not store secrets in frontend code.
Do not commit API keys.

---

# 11. Optional Apify/Bright Data Placeholders

Add disabled placeholder providers for Apify and Bright Data.

They should:
- be disabled by default
- include configuration documentation
- not pretend to work unless implemented
- explain intended purpose
- list compliance review requirement
- preserve adapter interface

Do not implement paid provider calls unless the project has explicit key/config and the implementation is straightforward.

---

# 12. Tests and Validation

Add or update tests for:

- provider adapter interface
- mock discovery provider
- discovery run creation
- discovery import summary
- saved search default creation
- deduplication by source URL
- deduplication by source listing ID
- last_seen_at update on rediscovery
- user notes/status preservation on update
- backyard/garage extraction from provider description
- missing API key disables provider gracefully
- discovery endpoint with mock provider

Suggested files:

- `tests/test_discovery_provider.py`
- `tests/test_mock_discovery.py`
- `tests/test_discovery_runs.py`
- `tests/test_saved_searches.py`
- `tests/test_discovery_deduplication.py`
- update scoring/parser tests if needed

Run:

```bash
pytest
```

Also run:

```bash
python -m compileall app
```

---

# 13. Documentation Updates

Update or create:

- `README.md`
- `AGENTS.md`
- `DATA_SOURCES.md`
- `SCRAPING_POLICY.md`
- optional `DISCOVERY.md`

README should explain:
- the app can now discover listings through provider adapters
- real discovery requires configured provider API keys unless using mock provider
- how to run mock discovery
- how to configure RentCast or the chosen provider
- how imported listings are deduplicated
- how backyard/garage are inferred
- why some listings are marked needs-review
- what is not implemented

DISCOVERY.md should explain:
- architecture
- provider adapter interface
- how to add a new provider
- environment variables
- discovery run lifecycle
- troubleshooting

AGENTS.md should say:
- do not add risky scraping without explicit review
- do not commit API keys
- keep providers disabled if not configured
- preserve provenance
- preserve user notes/status during deduplication
- add tests for every provider
- do not claim live scraping works unless tested

SCRAPING_POLICY.md should be updated to clarify:
- provider-based discovery is allowed when configured by the user
- high-risk scrapers remain disabled by default
- no CAPTCHA bypass or stealth automation
- user must review provider/source terms

---

# 14. Implementation Rules

- Preserve previous work.
- Keep the app runnable.
- Do not break dashboard, manual entry, paste import, CSV import, URL reference, browser clipper, scoring, benchmarks, exports, or backup.
- Do not implement CAPTCHA bypass.
- Do not implement stealth scraping.
- Do not implement proxy evasion.
- Do not commit API keys.
- Do not require an API key for the app to start.
- Mock discovery must work without external credentials.
- Real provider adapter must fail gracefully when not configured.
- Keep frontend vanilla JS/CSS/HTML.
- Keep source provenance complete.
- Keep scoring explainable.
- Preserve user-entered notes and decisions during listing updates.
- Be honest in docs about what works and what is planned.

---

# 15. Completion Audit

Before finishing, perform a final audit.

Use this table:

| Requirement | Status | Notes |
|---|---|---|
| Discovery architecture added | pass/partial/fail | ... |
| Provider interface added | pass/partial/fail | ... |
| RentCast or chosen API provider adapter added | pass/partial/fail | ... |
| Missing API key handled gracefully | pass/partial/fail | ... |
| Mock discovery provider works | pass/partial/fail | ... |
| Discovery run model added | pass/partial/fail | ... |
| Discovery endpoints added | pass/partial/fail | ... |
| Saved searches added | pass/partial/fail | ... |
| Default Orange County saved search added | pass/partial/fail | ... |
| Deduplication improved | pass/partial/fail | ... |
| Backyard/garage extraction applied to discovered listings | pass/partial/fail | ... |
| Dashboard discovery UI added | pass/partial/fail | ... |
| Provider config docs added | pass/partial/fail | ... |
| Tests added/updated | pass/partial/fail | ... |
| README updated | pass/partial/fail | ... |
| AGENTS.md updated | pass/partial/fail | ... |
| DATA_SOURCES.md updated | pass/partial/fail | ... |
| SCRAPING_POLICY.md updated | pass/partial/fail | ... |
| App still runs | pass/partial/fail | ... |

---

# 16. Final Response

When complete, summarize:

1. What changed
2. Whether automatic discovery now works
3. Which provider works without credentials
4. Which provider needs an API key
5. How to configure the API key
6. How to run discovery
7. How deduplication works
8. Tests run and results
9. Known limitations
10. The best next `/goal` to run

Also include:
- any manual setup needed
- any skipped provider integrations and why
- biggest remaining product risk
- highest-leverage next improvement

---

# 17. Recommended Next Goal After This

After this goal, recommend exactly one next goal.

Choose from:

## Option A: Scheduled Discovery and Alerts

Best if automatic discovery works and the user wants the app to actively monitor listings.

Goal:
- Add scheduled discovery runs.
- Add daily refresh.
- Add alert badges.
- Add stale listing detection.
- Add new match notifications in-dashboard.
- Add optional email/desktop notification later.

## Option B: Provider Expansion

Best if RentCast/mock works but coverage is weak.

Goal:
- Add Apify provider.
- Add Bright Data provider.
- Add property management site adapters.
- Add source coverage comparison.
- Add provider reliability stats.

## Option C: Touring and Application Workflow

Best if listing discovery is good and the user is ready to act.

Goal:
- Add contact tracker.
- Add tour scheduler.
- Add application checklist.
- Add pros/cons decision memo.
- Add final shortlist comparison.

End by recommending exactly one next goal and explain why.
