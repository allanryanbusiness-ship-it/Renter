# Goal: Build the Browser Clipping and Fast Listing Capture Workflow

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
- CSV import or placeholder
- URL reference support
- scoring system
- score breakdowns
- decision workflow
- needs-review logic
- source/provenance tracking

## Mission

Make it extremely fast for the user to capture rental listings while browsing real estate sites.

The user is searching for Orange County, California rental properties with:

- 3 bedrooms minimum
- backyard required
- garage required
- strong value/deal potential
- easy comparison across Zillow, Redfin, Realtor, Apartments.com, HotPads, Craigslist, Facebook Marketplace, property management sites, and manually found listings

The app should let the user capture listings in a safe, user-driven way without implementing risky scraping, CAPTCHA bypass, stealth automation, proxy evasion, or fake live integrations.

## Core Product Goal

Create a browser clipping workflow where the user can:

1. Visit a listing page in their normal browser.
2. Select useful listing text or copy page details.
3. Click a bookmarklet or use a clipping panel.
4. Send the page URL, page title, selected text, and optional notes to the local FastAPI app.
5. The app imports the clipped data using the existing paste parser and URL reference logic.
6. The listing appears in the dashboard with source provenance, evidence snippets, score breakdown, and needs-review badges.

This should make the app usable as a real rental-hunting command center even before live scraping exists.

---

# 1. Browser Bookmarklet

Create a bookmarklet-based capture flow.

Add a file such as:

- `static/js/bookmarklet.js`

Also add a generated bookmarklet snippet somewhere easy to copy, such as:

- dashboard UI section
- `README.md`
- `BOOKMARKLET.md`

The bookmarklet should capture:

- current page URL
- document title
- selected text
- optional page text fallback, if safe and reasonable
- timestamp
- source domain
- user note, via prompt or simple popup

The bookmarklet should send data to the local app endpoint.

Suggested endpoint:

- `POST /api/import/clip`

Request shape:

```json
{
  "source_url": "https://example.com/listing/123",
  "page_title": "3 Bed Home in Irvine",
  "selected_text": "3 beds, 2 baths, attached garage, private backyard...",
  "page_text": "",
  "source_domain": "example.com",
  "user_notes": "Looks promising",
  "captured_at": "2026-05-06T12:00:00Z"
}
```

Important:
- Keep the bookmarklet simple.
- Do not scrape protected pages in the background.
- Do not bypass login, CAPTCHA, paywalls, anti-bot systems, or browser protections.
- It is okay if some sites block cross-origin requests. Document fallback options.
- If direct POST from bookmarklet fails due to CORS/mixed-content issues, provide a fallback copy-to-clipboard workflow.

---

# 2. Clipping Import Endpoint

Implement:

- `POST /api/import/clip`

The endpoint should:

- accept captured page URL
- accept page title
- accept selected text
- accept optional page text
- accept optional user notes
- infer source name from domain
- preserve raw clipped text
- preserve selected text
- preserve source URL
- run deterministic extraction using the existing paste parser
- create or update a listing
- return import summary and created listing ID

Response should include:

```json
{
  "data": {
    "listing_id": 123,
    "source_name": "Zillow",
    "fields_extracted": [
      "price_monthly",
      "bedrooms",
      "bathrooms",
      "garage_status",
      "backyard_status"
    ],
    "needs_review": true,
    "warnings": [
      "Garage detected from text but needs manual verification",
      "Backyard evidence may be ambiguous"
    ]
  },
  "meta": {
    "import_type": "browser_clip"
  },
  "errors": []
}
```

---

# 3. Fallback Copy/Paste Clipper

Because some real estate sites may block direct bookmarklet posts or CORS, create a fallback workflow.

The bookmarklet should be able to:

- copy a structured JSON payload to clipboard, or
- open the local app with encoded clipped data in the URL hash/query, or
- show a text blob the user can paste into the app

Choose the most reliable approach for the existing app.

Add frontend support for importing this clipped payload.

Possible UI:

- “Import Browser Clip”
- textarea for clipped JSON/text
- button: “Import Clip”
- preview extracted fields
- confirm import

This is important because local browser security may make a one-click POST unreliable.

---

# 4. Dashboard Capture Panel

Add a section to the dashboard called something like:

- Browser Clipper
- Quick Capture
- Add From Browser
- Listing Clipper

It should include:

- explanation of how to use the bookmarklet
- copyable bookmarklet link or code
- fallback paste box for clipped payloads
- status message after successful import
- warning that this is user-driven capture, not automated scraping
- link to `BOOKMARKLET.md` if created

Keep the UI dark mode and consistent with the existing command-center design.

---

# 5. Source Inference Improvements

Improve domain-to-source inference.

Recognize at least:

- zillow.com → Zillow
- redfin.com → Redfin
- realtor.com → Realtor
- apartments.com → Apartments.com
- hotpads.com → HotPads
- craigslist.org → Craigslist
- facebook.com / marketplace.facebook.com → Facebook Marketplace
- property management domains → Property Management Site or Other

Create or update code such as:

- `app/sources/source_inference.py`
- or an existing source inference module

Preserve:
- source_domain
- source_name
- source_url
- source_type = browser_clip or url_reference

---

# 6. Duplicate Detection

Add basic duplicate detection for clipped listings.

Use simple signals:

- same source URL
- same normalized address if present
- same title + city + price
- same source listing ID if present later

Behavior:
- If exact source URL already exists, update the existing listing instead of creating duplicate.
- If possible duplicate is detected but not exact, create the listing but mark it `needs_review` and add warning.
- Preserve older notes and decision status when updating an existing listing.

Add tests for duplicate behavior.

---

# 7. Parser Improvements for Browser Clips

Improve deterministic extraction from clipped text.

Extract when possible:

- price_monthly
- bedrooms
- bathrooms
- square_feet
- address
- city
- state
- zip
- backyard_status
- backyard_evidence
- garage_status
- garage_evidence
- parking_details
- pet_policy
- laundry
- air_conditioning

Preserve exact evidence snippets.

Do not overstate certainty. If evidence is ambiguous:
- status should be unknown
- confidence should be lower
- next action should include manual verification

---

# 8. Security and Localhost Rules

Add basic guardrails.

The clipping endpoint should:

- accept local usage
- validate payload size
- reject extremely large payloads
- sanitize text fields before storing/rendering
- avoid executing any clipped HTML or script
- store text only
- not fetch external URLs server-side unless a future approved adapter explicitly does so

Document:
- the app stores user-clipped text
- it does not secretly scrape the page
- it does not bypass site protections
- it does not fetch protected pages in the background

---

# 9. Documentation

Create or update:

- `BOOKMARKLET.md`
- `README.md`
- `AGENTS.md`
- `SCRAPING_POLICY.md` if needed

## BOOKMARKLET.md should include:

- what the browser clipper does
- how to install the bookmarklet
- how to use it
- what data it captures
- what it does not do
- known limitations
- fallback workflow
- troubleshooting

## README.md should include:

- browser clipping as the recommended daily capture workflow
- how clipped listings are parsed and scored
- how to use fallback paste import
- how duplicate detection works
- how to verify backyard/garage evidence

## AGENTS.md should include:

- preserve user-driven capture model
- do not add background scraping without explicit review
- do not add CAPTCHA bypass or stealth automation
- all clipped data must preserve provenance
- sanitize clipped text before display
- add tests for parser and duplicate changes

---

# 10. Tests and Validation

Add or update tests for:

- clip import endpoint
- source inference
- duplicate detection by URL
- duplicate detection by title/city/price if practical
- parser extraction from clipped text
- evidence preservation
- payload size validation
- sanitization if implemented
- fallback clipped payload import

Suggested files:

- `tests/test_clip_import.py`
- `tests/test_source_inference.py`
- `tests/test_duplicate_detection.py`
- `tests/test_browser_clip_parser.py`

Run tests with:

```bash
pytest
```

Also run syntax/import checks if the project has them.

---

# 11. UX Acceptance Criteria

The dashboard should support this workflow:

1. User opens the dashboard locally.
2. User copies or installs bookmarklet.
3. User visits a listing page.
4. User selects listing text.
5. User runs bookmarklet.
6. Data is sent to the app or copied as fallback payload.
7. User imports the clip.
8. Listing appears in dashboard.
9. Listing has source URL and source badge.
10. Listing has extracted fields where possible.
11. Listing has backyard/garage evidence or needs-review badges.
12. Listing has score breakdown.
13. Duplicate source URL does not create duplicate listing.

---

# 12. Implementation Rules

- Preserve previous work.
- Keep the app runnable.
- Keep frontend vanilla JS, CSS, and HTML.
- Do not add a browser extension unless it is a clearly separated optional future path.
- Prefer bookmarklet plus fallback paste flow for MVP.
- Do not implement background scraping.
- Do not implement CAPTCHA bypass.
- Do not implement proxy evasion.
- Do not fetch listing pages server-side.
- Do not execute clipped HTML.
- Store clipped content as plain text.
- Keep all features honest and labeled.
- If a direct bookmarklet POST is unreliable due to CORS, prioritize the fallback clipboard/import workflow.
- Do not break existing manual, paste, CSV, URL reference, scoring, or decision workflow features.

---

# 13. Completion Audit

Before finishing, perform a final audit.

Use this table:

| Requirement | Status | Notes |
|---|---|---|
| Bookmarklet created | pass/partial/fail | ... |
| Clip import endpoint added | pass/partial/fail | ... |
| Fallback clipboard/paste workflow added | pass/partial/fail | ... |
| Dashboard capture panel added | pass/partial/fail | ... |
| Source inference improved | pass/partial/fail | ... |
| Duplicate detection added | pass/partial/fail | ... |
| Parser improved for clips | pass/partial/fail | ... |
| Payload validation added | pass/partial/fail | ... |
| Clipped text sanitized or safely rendered | pass/partial/fail | ... |
| BOOKMARKLET.md created | pass/partial/fail | ... |
| README updated | pass/partial/fail | ... |
| AGENTS.md updated | pass/partial/fail | ... |
| Tests added/updated | pass/partial/fail | ... |
| App still runs | pass/partial/fail | ... |

---

# 14. Final Response

When complete, summarize:

1. What changed
2. How to use the browser clipper
3. How to use the fallback workflow
4. Which files matter most
5. Tests run and results
6. Known limitations
7. The best next `/goal` to run

Also include:
- any manual setup needed for the bookmarklet
- whether direct bookmarklet POST works or fallback is preferred
- biggest remaining product risk
- highest-leverage next improvement

---

# 15. Recommended Next Goal After This

After this goal, recommend exactly one next goal.

Choose from:

## Option A: Market Benchmark Calibration

Best if scoring needs to become more accurate.

Goal:
- Research current Orange County 3-bedroom rental benchmarks by city from public/safe sources.
- Replace placeholder city benchmarks with sourced estimates.
- Add citations in documentation.
- Update scoring weights.
- Keep benchmarks editable.

## Option B: Deployment and Local Reliability

Best if the app needs to be used daily.

Goal:
- Add reliable local run scripts.
- Add backup/export.
- Add import/export JSON.
- Add Docker support if useful.
- Add persistent SQLite path configuration.
- Add app logs.
- Improve error handling.
- Prepare for Railway/VPS deployment if desired.

## Option C: Saved Searches and Alerts

Best if the app needs to become a true rental hunting assistant.

Goal:
- Add saved searches.
- Add manual check reminders.
- Add watchlist alerts based on imported data.
- Add “contact today” queue.
- Add calendar-like next action tracking.

End by recommending exactly one next goal and explain why.
