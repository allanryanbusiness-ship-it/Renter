# Goal: Calibrate Orange County Rental Market Benchmarks and Deal Scoring

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
- browser clipping/bookmarklet workflow
- scoring system
- score breakdowns
- decision workflow
- needs-review logic
- source/provenance tracking
- placeholder city benchmark file

## Mission

Improve the accuracy and usefulness of the rental deal scoring system for Orange County, California.

The user is searching for rental properties with:

- Orange County CA location
- 3 bedrooms minimum
- backyard required
- garage required
- strong value/deal potential
- easy comparison across clipped, pasted, manual, CSV, and URL-referenced listings

The current app may have placeholder city benchmark data. This goal should turn that into a more credible, transparent, editable benchmark system.

## Core Product Goal

Make the app better at answering:

1. Is this rental overpriced, fair, or unusually good value?
2. How does this listing compare to similar 3-bedroom rentals in the same Orange County city?
3. Is the score based on real benchmark data, placeholder data, or user-entered estimates?
4. Which listings are under market but need manual verification?
5. Which cities appear better value for the user’s requirements?

Do this without adding risky scraping, CAPTCHA bypass, stealth automation, proxy evasion, or fake live Zillow/Redfin integrations.

---

# 1. Benchmark Data Model

Create or improve an editable benchmark data structure.

Use a file such as:

- `app/data/city_benchmarks.json`

Each city benchmark should include:

- city
- county
- state
- median_rent_3br
- typical_low_3br
- typical_high_3br
- median_price_per_sqft
- typical_low_price_per_sqft
- typical_high_price_per_sqft
- benchmark_confidence
- data_source_type
- data_sources
- last_reviewed
- notes

Example shape:

```json
{
  "Irvine": {
    "city": "Irvine",
    "county": "Orange County",
    "state": "CA",
    "median_rent_3br": 4800,
    "typical_low_3br": 4200,
    "typical_high_3br": 5800,
    "median_price_per_sqft": 3.25,
    "typical_low_price_per_sqft": 2.75,
    "typical_high_price_per_sqft": 4.10,
    "benchmark_confidence": "medium",
    "data_source_type": "manual_research",
    "data_sources": [
      {
        "name": "Example Source",
        "url": "https://example.com",
        "accessed_at": "2026-05-06",
        "notes": "Replace with actual source notes"
      }
    ],
    "last_reviewed": "2026-05-06",
    "notes": "Editable benchmark. Verify periodically."
  }
}
```

If existing benchmark data exists, migrate it carefully instead of replacing blindly.

---

# 2. Research Current Orange County 3-Bedroom Rental Benchmarks

Research current rental benchmarks for common Orange County cities.

Important:
- Use public/safe sources only.
- Do not scrape protected pages.
- Do not bypass anti-bot systems.
- Do not use paid APIs unless already integrated.
- Do not claim precision that the sources do not support.

Research at least these cities:

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

For each city, try to estimate:

- typical 3-bedroom rent
- low-end 3-bedroom rent
- high-end 3-bedroom rent
- rough price per square foot if available
- confidence level
- notes on source quality

Acceptable source types may include:

- rental market reports
- public listing summary pages
- apartment/rental data aggregators
- manually reviewed public pages
- government/county datasets if relevant
- user-editable estimates when public data is weak

Document sources in:

- `MARKET_RESEARCH.md`

Each benchmark entry in the JSON should include source notes.

If exact 3-bedroom data is not available for a city, make a conservative estimate from available nearby or general rental data and mark confidence as low.

---

# 3. Benchmark Service

Create or update code such as:

- `app/services/benchmark_service.py`
- `app/benchmarks.py`
- or an appropriate existing module

The benchmark service should support:

- loading benchmark JSON
- normalizing city names
- retrieving benchmark for a listing city
- fallback to county-wide benchmark if city is missing
- returning benchmark confidence
- returning source notes
- validating benchmark file shape
- safe defaults if benchmark data is missing

Do not crash scoring if benchmark data is incomplete.

---

# 4. Deal Score Calibration

Update deal scoring to use the benchmark service.

Deal score should consider:

- listing rent versus city median 3-bedroom rent
- listing rent versus typical low/high range
- price per bedroom
- price per square foot, if square feet exists
- bedroom count relative to 3-bedroom baseline
- backyard/garage status
- confidence/completeness
- listing freshness

Suggested behavior:
- Below typical low range: high deal score, but add warning to verify listing quality or scam risk.
- Below median: positive score.
- Near median: neutral/fair score.
- Above median: lower deal score.
- Above typical high: strongly lower deal score unless listing has unusually strong features.
- Missing city benchmark: use county fallback and lower confidence.
- Missing square feet: do not fail, but reduce confidence/completeness.

Add reasons such as:
- “Rent is 12% below Irvine 3-bedroom benchmark”
- “Price per sqft is above city typical range”
- “Benchmark confidence is low, verify manually”
- “No city benchmark found, using county fallback”

---

# 5. Benchmark Transparency in API

Expose benchmark context in score breakdowns.

For each listing score breakdown, include:

- benchmark_city
- benchmark_used
- benchmark_confidence
- median_rent_3br
- typical_low_3br
- typical_high_3br
- rent_delta_vs_median
- rent_delta_percent
- price_per_sqft_delta if available
- benchmark_notes
- benchmark_sources if appropriate

Do not overload the frontend, but make the data available.

---

# 6. Dashboard Benchmark UI

Update the frontend so the user can understand deal score better.

Add or improve UI elements:

- benchmark badge on listing detail
- “vs city median” indicator
- under/fair/over market label
- warning for low-confidence benchmarks
- city comparison panel if practical
- filter or sort by “best below market”
- score explanation text that references benchmark data

Examples:
- “$400 below Irvine 3BR benchmark”
- “8% above Costa Mesa typical range”
- “Using low-confidence benchmark. Verify manually.”
- “No city benchmark found. County fallback used.”

Keep UI dark, clean, and command-center-like.

---

# 7. Benchmark Editor or Manual Override

Add a simple way to edit benchmark assumptions.

Choose one of these MVP approaches:

## Option A: JSON-only editor

Document clearly how to edit:

- `app/data/city_benchmarks.json`

Add validation command or test.

## Option B: Minimal dashboard editor

Add a simple UI panel to edit:
- city
- median 3BR rent
- typical low/high
- confidence
- notes

Then persist to JSON or database if safe.

Prefer Option A unless existing architecture makes Option B easy and reliable.

---

# 8. Tests and Validation

Add or update tests for:

- benchmark JSON loading
- city name normalization
- missing city fallback
- missing benchmark safe behavior
- rent below median scoring
- rent above median scoring
- low-confidence benchmark warnings
- score breakdown includes benchmark context
- placeholder/source notes are preserved

Suggested files:

- `tests/test_benchmarks.py`
- `tests/test_deal_score_calibration.py`
- update `tests/test_scoring.py`

Run:

```bash
pytest
```

Also run any existing app smoke tests or import checks.

---

# 9. Documentation Updates

Update or create:

- `MARKET_RESEARCH.md`
- `README.md`
- `AGENTS.md`
- `DATA_SOURCES.md` if needed

## MARKET_RESEARCH.md should include:

- research date
- sources used
- city-by-city benchmark notes
- confidence levels
- limitations
- how benchmarks should be updated later
- clear warning that rental markets change frequently

## README.md should explain:

- how benchmark-based deal scoring works
- how to interpret “below market”
- why low-confidence benchmarks require manual verification
- how to edit city benchmarks
- how to rerun tests
- current limitations

## AGENTS.md should say:

- benchmark data must include provenance
- do not fabricate precise market data
- mark estimates clearly
- update tests when scoring changes
- do not implement scraping or CAPTCHA bypass to collect benchmark data
- keep benchmark logic explainable

---

# 10. Implementation Rules

- Preserve previous work.
- Keep the app runnable.
- Do not break manual, paste, CSV, URL, browser clipper, scoring, or decision workflow features.
- Do not add paid APIs.
- Do not add risky scrapers.
- Do not bypass CAPTCHA or anti-bot systems.
- Do not claim benchmark precision beyond source quality.
- Use conservative estimates when exact data is unavailable.
- Label low-confidence data clearly.
- Store sources and last reviewed dates.
- Keep benchmark data editable.
- Keep frontend vanilla JS/CSS/HTML.
- Keep score reasons explainable.

---

# 11. Completion Audit

Before finishing, perform a final audit.

Use this table:

| Requirement | Status | Notes |
|---|---|---|
| Benchmark data model improved | pass/partial/fail | ... |
| Orange County city benchmarks researched | pass/partial/fail | ... |
| MARKET_RESEARCH.md created | pass/partial/fail | ... |
| Benchmark sources documented | pass/partial/fail | ... |
| Benchmark service added/updated | pass/partial/fail | ... |
| Deal score calibrated | pass/partial/fail | ... |
| Score breakdown includes benchmark context | pass/partial/fail | ... |
| Dashboard benchmark UI added | pass/partial/fail | ... |
| Benchmark editing/override documented or implemented | pass/partial/fail | ... |
| Tests added/updated | pass/partial/fail | ... |
| README updated | pass/partial/fail | ... |
| AGENTS.md updated | pass/partial/fail | ... |
| App still runs | pass/partial/fail | ... |

---

# 12. Final Response

When complete, summarize:

1. What changed
2. Which benchmark sources were used
3. Which cities have strongest confidence
4. Which cities have weakest confidence
5. How scoring changed
6. How to edit benchmark data
7. Tests run and results
8. Known limitations
9. The best next `/goal` to run

Also include:
- any benchmarks that need manual review
- biggest remaining product risk
- highest-leverage next improvement

---

# 13. Recommended Next Goal After This

After this goal, recommend exactly one next goal.

Choose from:

## Option A: Deployment and Local Reliability

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

## Option B: Saved Searches and Alerts

Best if the app needs to become a true rental hunting assistant.

Goal:
- Add saved searches.
- Add manual check reminders.
- Add watchlist alerts based on imported data.
- Add “contact today” queue.
- Add calendar-like next action tracking.

## Option C: Property Visit and Decision Toolkit

Best if the user is ready to tour/contact listings.

Goal:
- Add tour checklist.
- Add landlord/property manager contact tracker.
- Add deal memo export.
- Add pros/cons comparison.
- Add final decision scorecard.

End by recommending exactly one next goal and explain why.
