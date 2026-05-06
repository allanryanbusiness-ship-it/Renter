# Data Sources

## Research Goal

Evaluate current repo and service options for rental listing aggregation while avoiding fake claims about live Zillow, Redfin, or Realtor scraping support.

## Recommended for Real Integrations

### Bridge Interactive

- Best fit when the user has MLS or partner access.
- Useful for licensed listing access, Zillow public records, and approved Zestimate-related datasets through a formal workflow.
- Reference: <https://www.bridgeinteractive.com/developers/bridge-api/>

### RentCast

- Good candidate for a paid adapter when property, listing, and rent-estimate coverage is sufficient.
- Official developer docs exist and are more stable than reverse-engineered web scrapers.
- References:
  - <https://developers.rentcast.io/reference/introduction>
  - <https://help.rentcast.io/en/articles/7992900-rentcast-property-data-api>

### ATTOM

- Strong for public-record, property-detail, and rental valuation enrichment.
- Better as an enrichment and market-intelligence source than as a direct consumer listing scraper.
- References:
  - <https://api.developer.attomdata.com/docs>
  - <https://www.attomdata.com/solutions/property-data-api/how-it-works/>

### Public and Government Data

- HUD Fair Market Rent datasets are useful for baseline rent context.
- Census ACS API is useful for demographics and neighborhood context.
- Orange County Assessor parcel/property information is useful for public property validation.
- References:
  - <https://www.huduser.gov/portal/taxonomy/term/662>
  - <https://www.census.gov/programs-surveys/acs/data/data-via-api.html>
  - <https://www.ocassessor.gov/page/property-information-and-parcel-maps>

## Useful Repos as References, Not Default Integrations

### HomeHarvest

- Repo: <https://github.com/ZacharyHampton/HomeHarvest>
- Why it is useful:
  - Good example of canonical listing fields
  - Multi-source aggregation shape
  - Useful inspiration for field coverage such as pets, parking, tags, and estimates
- Why it is risky as a production dependency:
  - It relies on site scraping behavior that can change without notice
  - Its own docs mention site blocking and 403 responses
  - It should be treated as a reference implementation, not the app's compliance story

### `reteps/redfin`

- Repo: <https://github.com/reteps/redfin>
- Why it is useful:
  - Documents unofficial Redfin endpoint patterns
  - Helpful for understanding field naming and unofficial API shapes
- Why it is risky:
  - It is explicitly unofficial
  - The repo is comparatively stale
  - It should not be presented as a supported production path

## Services and Actors to Treat Carefully

### Apify Actors

- Apify itself is a legitimate platform for running scraping jobs, but actor quality and legal posture vary by actor.
- This app should only integrate Apify behind a separate adapter and user-supplied credentials after a source-specific review.
- No actor should be represented as "official" access to Zillow, Realtor.com, or Redfin unless that is actually documented by the source owner.
- References:
  - <https://docs.apify.com/>
  - Example actor page: <https://apify.com/scrapio/zillow-search-scraper/api>

## Sources to Keep Disabled by Default

- Direct Zillow HTML or internal endpoint scrapers
- Direct Redfin scraping adapters
- Direct Realtor.com scraping adapters
- Craigslist automation against listing content
- Any integration that depends on CAPTCHA solving, stealth browsers, proxy rotation, or anti-bot evasion

## Practical MVP Strategy

1. Start with demo data, manual entry, and CSV imports.
2. Add licensed/public APIs behind clean adapter interfaces.
3. Use public data for rent context and parcel validation.
4. Keep risky scrapers disabled until a compliant route is validated.

## Additional Market Context

- Realtor.com publishes Orange County market summaries that can help guide calibration of expectations without being a listing-ingestion path.
- Zillow and Redfin announced a 2025 rental partnership affecting multifamily listing distribution, which is a reminder that source overlap and syndication can distort duplicate detection.
- References:
  - <https://www.realtor.com/local/market/california/orange-county>
  - <https://investors.zillowgroup.com/investors/news-and-events/news/news-details/2025/Zillow-and-Redfin-partner-to-make-apartment-hunting-easier-and-give-listings-more-exposure/default.aspx>
