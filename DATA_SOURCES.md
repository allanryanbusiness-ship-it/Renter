# Data Sources Strategy

## Executive Summary

The durable MVP path is manual and semi-manual ingestion first, then licensed or approved APIs, with direct website scraping disabled until each source is reviewed. Zillow, Redfin, Realtor.com, Apartments.com, HotPads, Craigslist, and Facebook Marketplace all have meaningful legal, anti-bot, reliability, or account-risk concerns for automated collection. The app should therefore treat these sites as provenance references and user-entered sources today, not as live scraper targets.

The first implementation supports:

- Manual listing entry
- Browser clipping from the user's active tab
- Copy/paste listing import with deterministic local parsing
- CSV import from user-controlled exports
- URL reference capture without fetching the page
- Automatic discovery from approved/provider-based adapters
- Source/provenance metadata on every listing
- Public-market benchmark research stored as editable JSON with citations
- Disabled experimental scraper placeholders for future review

## Recommended MVP Source Strategy

| Rank | Source path | Recommendation | Reason |
|---|---|---|---|
| 1 | Manual entry | Use now | Highest compliance control, enough for active personal search workflows |
| 2 | Browser clipping | Use now | User-triggered URL/text/notes capture with fallback JSON import and no server-side fetch |
| 3 | Copy/paste import | Use now | User supplies text; parser stores raw text and evidence for verification |
| 4 | CSV import | Use now | Supports exports from spreadsheets, browser clips, or approved sources |
| 5 | URL reference | Use now | Preserves provenance without claiming extraction |
| 6 | Approved provider feed | Use now | Local/provider-style feed path exercises automatic discovery without external scraping |
| 7 | RentCast / ATTOM / Bridge | Evaluate next | More durable than brittle site scraping, but requires accounts and terms review |
| 8 | Apify / Bright Data / Oxylabs / ScraperAPI | Review case-by-case | Operationally strong but still needs source-level compliance review |
| 9 | Direct site scrapers | Keep disabled | High breakage and terms risk |

## Ranking of Data Source Options

### Best for this project now

- `Manual Import`: best for immediate Orange County comparison work.
- `Browser Clip`: fastest daily capture flow for pages the user is actively viewing; stores selected text, URL, source domain, and notes.
- `Paste Import`: useful for Zillow, Redfin, Realtor.com, property manager pages, emails, and texts where the user has already viewed the listing.
- `CSV Import`: useful for user-maintained spreadsheets and approved exports.
- `URL Reference`: useful when only a listing link exists and details are not yet verified.
- `Approved Demo Provider Feed`: automatic discovery from local provider-style data; useful for testing import, dedupe, and scoring without scraping.
- `City Benchmarks`: sourced public research for market comparison only; not listing ingestion and not a scraper.

### Best future data providers

- `RentCast`: active rental listing and rent-estimate API candidate. Its public docs include rental listings endpoints such as long-term rental listings, property records, rent estimates, and market data. Reference: <https://developers.rentcast.io/reference/introduction>
- `ATTOM`: strong property and rental valuation enrichment. ATTOM documents Rental AVM and property API endpoints. References: <https://api.developer.attomdata.com/docs>, <https://cloud-help.attomdata.com/article/501-rental-avm>
- `Bridge Interactive`: official MLS-oriented route where MLS access exists. Bridge says developers request data access from MLS customers and can access complementary datasets such as Zillow public records and Zestimates when authorized. Reference: <https://www.bridgeinteractive.com/developers/bridge-api/>

### Sources to treat as references only in the MVP

- Zillow
- Redfin
- Realtor.com
- Apartments.com
- HotPads
- Craigslist
- Facebook Marketplace
- Property management company pages unless their terms allow automated access

## GitHub / OSS Repository Landscape

### `ZacharyHampton/HomeHarvest`

- URL: <https://github.com/ZacharyHampton/HomeHarvest>
- Language: Python
- Sites/sources: Realtor.com, with historical/claimed Zillow, Redfin, and Realtor.com support in package/search-result descriptions
- Claims: real estate scraping library that formats property data in MLS style and supports CSV/Excel/Pandas outputs
- Useful parts: field vocabulary, CLI/API shape, export workflow ideas, normalization inspiration
- Risks: site behavior changes, scraping terms, blocking, and reliance on unofficial source behavior
- Recommendation: reference, do not use as a default dependency
- Maintenance notes: GitHub topic/search results surfaced activity in late 2025, but that does not make source access compliant

### `reteps/redfin`

- URL: <https://github.com/reteps/redfin>
- Language: Python
- Sites/sources: Redfin unofficial API
- Claims: Python wrapper around Redfin's unofficial API
- Useful parts: illustrates older unofficial endpoint shapes
- Risks: unofficial, stale, tied to private Redfin behavior, prohibited without permission under Redfin terms
- Recommendation: reference only
- Maintenance notes: GitHub search surfaced last update around July 2023

### `ryansherby/RedfinScraper`

- URL: <https://github.com/ryansherby/RedfinScraper>
- Language: Python
- Sites/sources: Redfin
- Claims: scrapes Redfin data
- Useful parts: historical example of basic Redfin extraction
- Risks: stale, likely brittle, no compliance story
- Recommendation: avoid
- Maintenance notes: GitHub topic results surfaced last update around August 2023

### `scrapfly/scrapfly-scrapers`

- URL: <https://github.com/scrapfly/scrapfly-scrapers>
- Language: Python
- Sites/sources: many sites; includes Zillow, Redfin, Realtor.com, and other real estate examples
- Claims: educational scrapers using the ScrapFly API and Python
- Useful parts: educational examples of parsing public pages and nested data
- Risks: requires ScrapFly service; examples emphasize bypass/blocking infrastructure; still needs source-specific legal review
- Recommendation: reference only for adapter shape and parsing patterns

### `oxylabs/scraping-real-estate-data-with-python`

- URL: <https://github.com/oxylabs/scraping-real-estate-data-with-python>
- Language: Python
- Sites/sources: Redfin via Oxylabs Web Scraper API
- Claims: guide for extracting public Redfin data using Oxylabs
- Useful parts: shows commercial scraper API integration pattern
- Risks: paid provider dependency, source terms still matter, not an official Redfin API
- Recommendation: reference only unless a reviewed commercial-provider adapter is approved

### `brightdata/real-estate-ai-agent`

- URL: <https://github.com/brightdata/real-estate-ai-agent>
- Language: Python
- Sites/sources: Bright Data MCP / structured web data workflow
- Claims: extracts real estate property data as structured JSON using AI agents and Bright Data
- Useful parts: shows agentic extraction and structured JSON workflow
- Risks: depends on Bright Data and an LLM stack; unnecessary for MVP; compliance review still required
- Recommendation: avoid for MVP, reference later if a Bright Data integration is approved
- Maintenance notes: GitHub topic search surfaced update around July 2025

### `harry-s-grewal/mls-real-estate-scraper-for-realtor.ca`

- URL: <https://github.com/harry-s-grewal/mls-real-estate-scraper-for-realtor.ca>
- Language: Python
- Sites/sources: Realtor.ca, not U.S. Realtor.com
- Claims: Canadian MLS/Realtor.ca scraper
- Useful parts: general real estate extraction shape
- Risks: wrong market for Orange County, source-specific terms, stale
- Recommendation: avoid
- Maintenance notes: GitHub topic search surfaced update around September 2023

### Recent low-signal Zillow scraper repos

- Examples surfaced through GitHub topic/search results include repos such as `zillow-explorer`, `zillow-zip-code-search-scraper`, and Zillow agent/manager scrapers.
- Language: often Python or unspecified
- Sites/sources: Zillow
- Claims: fast property/listing extraction
- Useful parts: almost none for this app without careful code review
- Risks: thin wrappers, possible spam repos, brittle endpoint assumptions, possible paid API funnels, no compliance story
- Recommendation: avoid

### CAPTCHA / anti-bot examples

Search results and scraping-provider pages commonly mention proxies, unblockers, CAPTCHA handling, browser fingerprinting, or anti-bot infrastructure. This project should not adopt 2Captcha, CapSolver, Anti-Captcha, stealth browser profiles, deceptive fingerprints, or proxy rotation as a strategy for consumer real estate sites.

## Automatic Discovery Implementation

The app now includes an approved/provider-based discovery path:

- `GET /api/discovery/providers` lists provider adapters and configuration state.
- `POST /api/discovery/run` runs selected providers.
- `GET /api/discovery/runs` reads persisted discovery run history.
- `GET /api/discovery/runs/{id}` reads one persisted run.
- `GET /api/saved-searches`, `POST /api/saved-searches`, `PUT /api/saved-searches/{id}`, and `DELETE /api/saved-searches/{id}` manage saved searches.
- `mock` works without credentials and returns local demo candidates.
- `approved_demo_feed` is enabled by default and reads [app/data/approved_provider_feed.json](app/data/approved_provider_feed.json).
- `rentcast` is disabled unless `RENTAL_DASHBOARD_RENTCAST_ENABLED=true` and `RENTCAST_API_KEY` or `RENTAL_DASHBOARD_RENTCAST_API_KEY` are set.
- `apify` and `brightdata` are disabled placeholders only.
- Discovery imports candidates through the same provenance, import-run, dedupe, and scoring path as other ingestion methods.
- Exact duplicate updates preserve user notes, decision status, watchlist status, and private notes.

This is not website scraping. The mock/local feed paths are demo/provider-style data; RentCast is a provider API adapter that requires user credentials and terms review.

See [DISCOVERY.md](DISCOVERY.md) and [AUTOMATIC_LISTING_DISCOVERY.md](AUTOMATIC_LISTING_DISCOVERY.md) for setup and audit details.

## Commercial Provider Landscape

### Bright Data

- Data: website scrapers, datasets, proxy/unblocker infrastructure, including Zillow-oriented offerings and real estate datasets
- Rental support: Zillow scraper pages describe rental-relevant fields; exact coverage depends on product and plan
- Cost/complexity: commercial account, API keys, source review, potential enterprise pricing
- Compliance concerns: Bright Data markets compliance, but the app still needs source-specific review and approved use
- Reliability: likely stronger than DIY scraping
- Recommended use: possible future provider adapter, disabled until approved
- References: <https://brightdata.com/products/data-collector/website/zillow>, <https://brightdata.com/blog/web-data/best-zillow-scrapers>

### Apify

- Data: actors for Zillow, Realtor.com, Redfin, and multi-site real estate scraping
- Rental support: some actors explicitly claim rental listing support
- Cost/complexity: pay-per-use actors, actor-specific quality, API token required
- Compliance concerns: actors are marketplace/community products unless clearly official; review each actor separately
- Reliability: varies by actor
- Recommended use: future adapter only after actor review
- References: <https://docs.apify.com/>, <https://apify.com/whitewalk/real-estate-scraper>, <https://blog.apify.com/realtor-com-data-scraper/>

### ScraperAPI

- Data: web scraping API and real estate examples
- Rental support: its real estate solution page references historical/current property prices, sales, rentals, and Zillow/Idealista scraper APIs
- Cost/complexity: paid API key, integration work, source review
- Compliance concerns: still not official source access
- Reliability: stronger than DIY HTTP requests, still subject to source changes
- Recommended use: future provider adapter for approved targets only
- References: <https://docs.scraperapi.com/getting-started/overview>, <https://scraperapi.io/solutions/real-estate-data-collection/>

### Oxylabs

- Data: Web Scraper API with real estate target docs; search results show Redfin and Apartments-oriented targets
- Rental support: provider positions its scraper API for real estate URLs and property pages
- Cost/complexity: paid account and credentials
- Compliance concerns: public-data and source-specific terms still need review
- Reliability: high operational maturity, not official listing access
- Recommended use: future adapter if a paid provider route is accepted
- References: <https://developers.oxylabs.io/scraping-solutions/web-scraper-api>, <https://developers.oxylabs.io/scraping-solutions/web-scraper-api/targets/real-estate>

### Search APIs: SerpAPI, SearchAPI, and similar

- Data: search-result snippets and structured search pages; SearchAPI advertises a Zillow API for sale, rental, and sold properties
- Rental support: SearchAPI claims rental search support; generic search APIs can surface listing URLs/snippets
- Cost/complexity: API key, paid usage, result normalization
- Compliance concerns: source and search provider terms must be reviewed; snippets may be incomplete
- Reliability: good for discovery, weak for complete property details
- Recommended use: future URL discovery, not canonical listing ingestion
- Reference: <https://www.searchapi.io/zillow-api>

### RapidAPI real estate endpoints

- Data: marketplace APIs for Zillow-like or real estate endpoints
- Rental support: varies by publisher
- Cost/complexity: easy signup but uneven quality and unclear source rights
- Compliance concerns: many endpoints appear to be unofficial scrapers
- Reliability: mixed
- Recommended use: avoid unless the endpoint publisher and source rights are verified

### RentCast

- Data: property records, rental listings, rent estimates, market stats
- Rental support: yes, including rental listing endpoints in public API docs
- Cost/complexity: API key and plan review
- Compliance concerns: review RentCast license for personal or commercial use
- Reliability: stronger than scraping for this product's likely needs
- Recommended use: strongest future API candidate
- References: <https://developers.rentcast.io/reference/introduction>, <https://help.rentcast.io/en/collections/4081100-rentcast-api>

### ATTOM

- Data: property, owner, valuation, tax, parcel, and Rental AVM data
- Rental support: Rental AVM, not necessarily active consumer listings
- Cost/complexity: commercial API
- Compliance concerns: license scope and redistribution rights
- Reliability: strong enrichment source
- Recommended use: future enrichment and rent-context adapter
- References: <https://api.developer.attomdata.com/docs>, <https://www.attomdata.com/solutions/property-data-api/how-it-works/>

### Bridge Interactive

- Data: MLS data access and complementary datasets when authorized
- Rental support: depends on MLS/feed permissions
- Cost/complexity: requires MLS/customer approval
- Compliance concerns: strongest official route, but permissions are gated
- Reliability: high if access is granted
- Recommended use: future official-listing route
- Reference: <https://www.bridgeinteractive.com/developers/bridge-api/>

## Manual and Semi-Manual Workflows

### Manual listing entry

The user enters structured fields such as title, city, price, bedrooms, bathrooms, backyard, garage, pets, URL, and notes. This is the safest active workflow.

### Copy/paste import

The user pastes listing text from a page, email, text message, or property manager post. The local parser extracts obvious fields and stores raw text plus evidence. The user should verify uncertain fields.

### Browser clipping

The user clicks the bookmarklet while viewing a listing page. The bookmarklet captures the current URL, title, selected text or limited visible-text fallback, source domain, timestamp, and optional note, then posts to `POST /api/import/clip` or copies fallback JSON for the dashboard import box. No page fetch occurs on the server.

### URL reference capture

The user saves a URL with optional title/notes. The app infers source from the domain and marks the listing `needs_manual_review`. No page fetch occurs.

### CSV import

The user pastes or uploads CSV text from a controlled export. The importer maps common columns and preserves unknown columns in `raw_payload_json`.

### Screenshots and notes

The current model can store notes and raw text. A future attachment workflow could store screenshots manually for human review, without OCR automation unless explicitly added and reviewed.

### Market benchmark research

The app uses [app/data/city_benchmarks.json](app/data/city_benchmarks.json) for editable Orange County 3-bedroom rent assumptions. Current source notes are documented in [MARKET_RESEARCH.md](MARKET_RESEARCH.md). Benchmarks should remain manually reviewed or sourced from approved/public datasets; do not add background scraping to refresh them.

### Manual change tracking

Until adapters mature, users can re-import a pasted listing or CSV row and compare notes manually. A future snapshot table can track price/status deltas.

## Compliance and Reliability Risks

- Zillow terms prohibit automated queries, screen/database scraping, robots, crawlers, and CAPTCHA bypass activity on the services. Reference: <https://www.zillow.com/z/corp/terms/>
- Redfin terms prohibit automated crawling/querying and scraping without express written permission. Reference: <https://www.redfin.com/about/terms-of-use>
- Realtor.com terms prohibit scraping and derivative reuse of Move Network content without express written permission. Reference: <https://www.realtor.com/terms-of-service/>
- Craigslist terms prohibit collecting content through robots, spiders, scripts, scrapers, crawlers, or equivalent manual techniques without a license. Reference: <https://www.craigslist.org/about/terms.html>
- Apartments.com terms restrict reuse of site materials outside personal/noncommercial use without prior written consent. Reference: <https://www.apartments.com/about/terms-of-service>
- Meta automated data collection terms require express written permission for automated data collection from Meta products. Reference: <https://www.facebook.com/legal/automated_data_collection_terms>

## Clear Next Steps

1. Keep manual, paste, CSV, and URL-reference ingestion as the supported MVP data paths.
2. Add editing workflows so pasted/CSV fields can be corrected after import.
3. Add listing snapshots for price/status change tracking.
4. Evaluate RentCast as the first approved API adapter.
5. Evaluate ATTOM for rent context and property enrichment.
6. Evaluate Bridge Interactive only if MLS access is realistic.
7. Keep all direct site scrapers disabled until a written review approves a specific source and implementation.
