# Product Spec

## Product Goal

Build a single-page dashboard that helps compare Orange County rental properties for a renter looking for at least 3 bedrooms, a backyard, and a garage.

## Primary User

- Household searching across Orange County, California
- Comparing scattered listings from several sources
- Needing a consistent view even when automated collection is unreliable or blocked

## Core User Workflows

### 1. Open Dashboard

The user lands on a fullscreen dashboard and immediately sees:

- Deal ranking
- Property cards
- Comparison table
- Active search criteria
- Manual add form

### 2. Compare Listings

The user compares listings by:

- Monthly price
- Bedrooms and bathrooms
- Square footage
- City and neighborhood
- Backyard and garage availability
- Pets allowance
- Listing source and URL
- Personal notes

### 3. Filter for Must-Haves

The dashboard defaults to Orange County with:

- `min_bedrooms = 3`
- `require_backyard = true`
- `require_garage = true`

### 4. Identify Best Deals

The app ranks properties using a weighted score composed of:

- Price efficiency
- Space
- Location fit
- Feature match
- Listing freshness
- Data confidence

### 5. Recover When Scraping Fails

If a source is blocked or unsupported, the user can:

- Paste a property URL
- Paste listing details manually
- Upload or transform CSV data later via the adapter pipeline

## MVP Non-Goals

- Full automation across every rental site
- CAPTCHA bypass or stealth scraping
- Multi-user auth
- Background schedulers
- Full listing-change history diffing

