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
