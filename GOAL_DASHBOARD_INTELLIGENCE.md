# Goal: Build the Rental Dashboard Intelligence Layer and Deal Review Workflow

You are working in an existing FastAPI rental property dashboard project.

The project already has:
- FastAPI backend
- separate frontend files:
  - templates/index.html
  - static/js/app.js
  - static/css/styles.css
- dark-mode single-page dashboard foundation
- source/data strategy documents
- adapter architecture
- manual entry support
- paste import support
- CSV import support or placeholder
- URL reference support
- normalized listing model/schema
- basic scoring

## Mission

Turn the project into a genuinely useful rental-hunting command center for Orange County, California.

The user is looking for rental properties with:
- Orange County CA location
- 3 bedrooms minimum
- backyard required
- garage required
- strong value/deal potential
- easy comparison across listings
- confidence-aware ranking when data is incomplete

The app should help the user answer:

1. Which properties are worth looking at first?
2. Which listings match the hard criteria?
3. Which listings are promising but need manual verification?
4. Which listings are overpriced?
5. Which listings are missing key information?
6. Which sources are most reliable?
7. Which properties should be watched, rejected, contacted, or toured?

## Core Principle

Make the dashboard useful even before live scraping exists.

The app should work well with:
- manual entries
- pasted listing text
- CSV imports
- saved listing URLs
- future adapters

Do not implement risky scraping, CAPTCHA bypass, stealth automation, proxy evasion, or fake live Zillow/Redfin functionality.

## Deliverables

Create or update the following areas.

---

# 1. Scoring System Upgrade

Update the scoring engine so every listing receives a detailed, explainable score.

Create or update files such as:

- `app/scoring.py`
- `app/schemas.py`
- `app/models.py`
- `app/services/scoring_service.py` if appropriate
- tests for scoring behavior

## Required Scores

Each listing should have:

### A. Match Score

Measures how closely the listing matches the user’s hard criteria.

Criteria:
- Orange County CA
- 3+ bedrooms
- backyard confirmed yes
- garage confirmed yes

Important:
- Confirmed yes should score highest.
- Unknown should score below yes but above no.
- Confirmed no should heavily penalize the listing.
- Listings outside Orange County should be strongly penalized.
- Listings under 3 bedrooms should be strongly penalized.

### B. Deal Score

Measures whether the listing looks like a good value.

Use available fields:
- monthly rent
- bedrooms
- bathrooms
- square feet
- city
- price per bedroom
- price per square foot
- data completeness
- listing freshness
- source confidence
- backyard/garage status

Since we may not have real city benchmark data yet, implement a placeholder benchmark system that can be edited later.

Suggested benchmark structure:
- `app/data/city_benchmarks.json`
- keyed by Orange County city
- approximate placeholder fields:
  - median_rent_3br
  - median_price_per_sqft
  - confidence
  - notes

Do not claim benchmark data is authoritative unless it is sourced. Label it as placeholder/sample data.

### C. Confidence Score

Measures how much the app should trust the listing data.

Factors:
- manual verified fields
- source type
- explicit evidence for backyard/garage
- raw text present
- source URL present
- missing fields
- imported from CSV versus pasted text versus manual entry

### D. Completeness Score

Measures how complete the listing is.

Important fields:
- price
- bedrooms
- bathrooms
- square feet
- city
- address
- backyard status
- garage status
- source URL
- description/raw text

### E. Freshness Score

Measures how recently the listing was imported or updated.

Use:
- first_seen_at
- last_seen_at
- imported_at
- updated_at

If real listing freshness is unknown, use import freshness and clearly label it as such.

---

# 2. Explainable Score Breakdown

Every listing should expose a clear explanation of why it received its scores.

Add an endpoint such as:

- `GET /api/listings/{id}/score-breakdown`

Or include score breakdown in:

- `GET /api/listings`

Each score breakdown should include:

```json
{
  "match_score": 87,
  "deal_score": 74,
  "confidence_score": 68,
  "completeness_score": 81,
  "freshness_score": 92,
  "overall_score": 79,
  "reasons": [
    "Meets 3+ bedroom requirement",
    "Backyard is confirmed from pasted description",
    "Garage is unknown, needs manual verification",
    "Price appears below placeholder city benchmark",
    "Square footage is missing, reducing confidence"
  ],
  "warnings": [
    "Backyard evidence may refer to shared patio, verify manually",
    "Benchmark data is placeholder only"
  ],
  "next_actions": [
    "Verify garage availability",
    "Check listing source URL",
    "Contact property manager"
  ]
}

---

# 3. Listing Decision Workflow

Add a practical workflow for the user to manage each listing.

Each listing should support a status such as:

- new
- promising
- needs_review
- contacted
- tour_scheduled
- rejected
- archived

Add fields if missing:
- decision_status
- decision_reason
- priority
- next_action
- next_action_due_date
- contact_name
- contact_phone
- contact_email
- tour_date
- user_rating
- private_notes

Add or update endpoints:

- `PATCH /api/listings/{id}/decision`
- `PATCH /api/listings/{id}/notes`
- `PATCH /api/listings/{id}/watchlist`

The dashboard should allow changing at least:
- decision status
- priority
- notes
- watchlist

Keep this simple and reliable.

---

# 4. Dashboard UI Upgrade

Update the single-page dark-mode dashboard so it feels like a serious rental command center.

Maintain:
- separate HTML, CSS, JS files
- no React
- no frontend build step
- clean vanilla JS

## Required UI Sections

### A. Top Summary Bar

Show:
- total listings
- strong matches
- needs review
- average rent
- lowest rent
- best deal score
- watched listings

### B. Search Criteria Panel

Show current criteria:
- Orange County CA
- 3+ bedrooms
- backyard required
- garage required

Allow editing:
- max price
- preferred cities
- allow unknown backyard yes/no
- allow unknown garage yes/no

### C. Ranked Deal Queue

A prioritized list of properties sorted by overall score.

Each item should show:
- title/address
- city
- rent
- beds/baths/sqft
- backyard badge
- garage badge
- overall score
- match score
- deal score
- confidence score
- decision status
- next action

### D. Listing Detail Drawer or Expanded Card

When user clicks a listing, show:
- score breakdown
- evidence for backyard/garage
- raw imported text if available
- source URL
- notes
- decision controls
- next action controls

If a drawer is too much, use expandable cards.

### E. Comparison Table

Show key fields across listings:
- rent
- beds
- baths
- sqft
- price per bedroom
- price per sqft
- backyard
- garage
- source
- confidence
- status

### F. Import Panel

Keep or improve:
- paste import
- manual add
- URL reference
- CSV import if implemented

### G. Filters and Sort

Filters:
- city
- max price
- backyard yes/unknown
- garage yes/unknown
- source
- decision status
- watchlist
- needs review

Sort:
- overall score
- deal score
- match score
- confidence
- price low to high
- newest
- completeness

---

# 5. Needs Review Intelligence

Add logic to identify listings that may be promising but need manual checking.

A listing should be marked or suggested as `needs_review` when:
- bedrooms and price look good
- backyard is unknown
- garage is unknown
- source URL exists but details are incomplete
- raw text suggests possible yard/garage but confidence is low
- city is in Orange County but address is incomplete

Expose this in the UI with clear badges:
- Verify backyard
- Verify garage
- Check source
- Missing sqft
- Possibly good deal

---

# 6. Evidence Extraction Improvements

Improve deterministic parsing for pasted listing text.

Look for backyard evidence:
- backyard
- back yard
- private yard
- fenced yard
- patio
- outdoor space
- garden
- lawn
- deck
- courtyard

Look for garage evidence:
- garage
- attached garage
- detached garage
- 2 car garage
- two car garage
- parking garage
- covered parking
- carport

Important:
- Preserve the exact phrase or text snippet that triggered the detection.
- Do not overstate uncertain matches.
- If phrase is ambiguous, mark as unknown or needs review.

Add parser tests for common examples.

---

# 7. City Benchmark Placeholder

Create a simple editable benchmark file:

- `app/data/city_benchmarks.json`

Include a handful of Orange County cities such as:
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

Use placeholder/sample benchmark values only if necessary.

Clearly mark:
- these are editable placeholder benchmarks
- not authoritative
- should be replaced later with sourced market data

Update `README.md` to explain this.

---

# 8. API Cleanup

Make sure API responses are consistent.

Recommended response structure:

```json
{
  "data": {},
  "meta": {},
  "errors": []
}

Do not do a giant rewrite if the app already works, but improve consistency where practical.

Add API docs comments or clear route names.

---

# 9. Tests and Validation

Add or update tests for:

- scoring hard criteria
- unknown backyard/garage behavior
- confirmed no backyard/garage penalties
- price per bedroom
- price per square foot
- confidence score
- paste evidence extraction
- decision status update
- URL reference behavior if not already tested

Use pytest if available. If not available, add it minimally.

Suggested tests:

- `tests/test_scoring.py`
- `tests/test_paste_import.py`
- `tests/test_decision_workflow.py`
- `tests/test_url_reference.py`

Make tests runnable with:

```bash
pytest

---

# 10. Documentation Updates

Update:

- `README.md`
- `AGENTS.md`
- `DATA_SOURCES.md` only if needed
- `SCRAPING_POLICY.md` only if needed

## README should explain:

- what the scoring means
- why unknown backyard/garage does not equal no
- how to use the deal queue
- how to use needs-review badges
- how to edit city benchmark placeholders
- current limitations
- next recommended development goals

## AGENTS.md should tell future agents:

- scoring must remain explainable
- do not hide score logic in frontend only
- preserve evidence text
- do not claim placeholder benchmark data is real market data
- add tests when changing scoring or parser logic
- maintain separate HTML/CSS/JS files unless explicitly told otherwise
- do not add risky scraping, CAPTCHA bypass, stealth automation, or proxy evasion
- update documentation when scoring, parsing, or source behavior changes

---

# 11. Implementation Sequence

Follow this order unless the existing repo makes a different order obviously better:

1. Inspect the current repo structure.
2. Read existing `README.md`, `AGENTS.md`, `DATA_SOURCES.md`, and `SCRAPING_POLICY.md`.
3. Inspect existing models, schemas, routes, scoring, and frontend files.
4. Extend the existing data model carefully.
5. Add or improve scoring logic.
6. Add explainable score breakdown.
7. Add decision workflow fields and endpoints.
8. Improve paste evidence extraction.
9. Add city benchmark placeholder file.
10. Update the frontend dashboard sections.
11. Add or update tests.
12. Update documentation.
13. Run syntax checks and tests.
14. Run the app or perform a smoke test if practical.
15. Complete the final audit.

---

# 12. Implementation Rules

- Preserve good work from previous goals.
- Do not rewrite the entire project unless absolutely necessary.
- Keep the app runnable.
- Keep dependencies light.
- Prefer deterministic parsing over paid AI calls.
- Do not use external paid APIs.
- Do not require API keys for the MVP.
- Do not claim live scraping works unless verified.
- Do not implement CAPTCHA bypass, stealth scraping, proxy evasion, browser fingerprint evasion, or credential-based scraping.
- Treat placeholder city benchmarks as sample editable data, not market truth.
- Keep scoring explainable.
- Preserve raw imported text and evidence snippets.
- Use clear error messages.
- Keep frontend state simple and understandable.
- Avoid fake buttons or fake features. If something is not fully implemented, label it clearly.
- Maintain the dark-mode single-page command-center design.

---

# 13. Completion Audit

Before finishing, perform a final audit.

Use this table:

| Requirement | Status | Notes |
|---|---|---|
| Scoring system upgraded | pass/partial/fail | ... |
| Score breakdown available | pass/partial/fail | ... |
| Decision workflow added | pass/partial/fail | ... |
| Dashboard summary bar added | pass/partial/fail | ... |
| Ranked deal queue added | pass/partial/fail | ... |
| Detail drawer or expandable details added | pass/partial/fail | ... |
| Comparison table improved | pass/partial/fail | ... |
| Filters and sorting improved | pass/partial/fail | ... |
| Needs-review logic added | pass/partial/fail | ... |
| Evidence extraction improved | pass/partial/fail | ... |
| City benchmark placeholder added | pass/partial/fail | ... |
| Tests added/updated | pass/partial/fail | ... |
| README updated | pass/partial/fail | ... |
| AGENTS.md updated | pass/partial/fail | ... |
| App still runs | pass/partial/fail | ... |

---

# 14. Final Response

When complete, summarize:

1. What changed
2. How to run it
3. Which files matter most
4. Which limitations remain
5. The best next `/goal` to run

Also include:

- any tests run and results
- any tests not run and why
- any files that need manual review
- the biggest remaining product risk
- the highest-leverage next improvement

---

# 15. Recommended Next Goal After This

After this goal is complete, recommend one of these next goals depending on what seems most valuable:

## Option A: Browser Clipping / Bookmarklet Workflow

Best if the dashboard needs easier data capture.

Possible next goal:
- Add a bookmarklet or browser clipping workflow that lets the user save a listing URL, title, selected text, and notes into the app.
- Keep it compliant and user-driven.
- No background scraping or CAPTCHA bypass.

## Option B: Market Benchmark Calibration

Best if scoring needs to become smarter.

Possible next goal:
- Research current Orange County 3-bedroom rental benchmarks by city using public/safe sources.
- Replace placeholder city benchmarks with sourced estimates.
- Add citations in documentation.
- Update scoring weights.

## Option C: Deployment and Local Reliability

Best if the app needs to be usable daily.

Possible next goal:
- Add local run scripts.
- Add backup/export.
- Add Docker support if useful.
- Add persistent SQLite path configuration.
- Add error handling and logs.
- Prepare for Railway/VPS deployment if desired.

End by recommending exactly one next goal and explain why.
