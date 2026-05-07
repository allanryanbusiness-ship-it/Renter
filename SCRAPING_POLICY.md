# Scraping and Ingestion Policy

## Intent

This project is intended to collect and compare rental listings through lawful, transparent, and reviewable data paths. It should respect site terms, robots.txt, rate limits, applicable law, and source-specific licensing.

## Allowed MVP Paths

- Manual entry by the user
- Browser clipping initiated by the user from their active browser tab
- Copy/paste import of user-provided listing text
- CSV import from user-controlled or approved exports
- URL reference capture without fetching or scraping the target page
- Automatic discovery from approved local feeds or provider APIs after review
- Approved public datasets and commercial APIs after review

## Prohibited Paths

- CAPTCHA bypass
- Stealth evasion
- Deceptive browser fingerprints
- Credential abuse
- Account sharing or session theft
- Proxy rotation intended to bypass source protections
- Automated collection from sites where terms or review prohibit it

## High-Risk Scrapers

High-risk scrapers must be disabled by default. This includes direct Zillow, Redfin, Realtor.com, Apartments.com, HotPads, Craigslist, and Facebook Marketplace automation unless a source-specific review approves a compliant implementation.

Any future scraper must document:

- Source URL and source owner
- Terms review
- Robots.txt review
- Rate limits and crawl scope
- Whether authentication is involved
- What data is collected
- What provenance is stored
- How failures and blocks are handled
- Why the collection path is allowed

## Provenance Requirements

Every listing should store provenance metadata:

- `source_name`
- `source_type`
- `source_url`
- `source_domain`
- `source_listing_id` when available
- `source_confidence`
- `first_seen_at`
- `last_seen_at`
- `imported_at`
- `discovery_run_id` for automatic discovery imports
- `raw_text` when pasted
- `raw_payload_json` for imports and adapters

## Browser Clipping Rules

The browser clipper is allowed because it is user-driven capture from the user's active page. It must remain narrow:

- It may capture the current page URL, title, selected text, limited visible text fallback, source domain, timestamp, and user notes.
- It may send that payload to `POST /api/import/clip` or copy fallback JSON for paste import.
- It must store clipped content as sanitized plain text.
- It must not execute clipped HTML or script.
- It must not fetch the listing page from the server.
- It must not bypass login walls, paywalls, CAPTCHA, anti-bot systems, rate limits, or browser protections.
- It must preserve raw clipped text, source URL, source domain, and evidence snippets for review.

## Market Benchmark Research Rules

Benchmark research may use public pages, official datasets, and approved APIs only. It must remain manual/reviewed unless a future source-specific approval adds an automated adapter.

- Do not add crawling, CAPTCHA bypass, stealth automation, or proxy evasion to refresh benchmarks.
- Do not claim a benchmark is precise when it is a public-page estimate or manually synthesized assumption.
- Store source URL, source name, accessed date, confidence, and notes in `app/data/city_benchmarks.json`.
- Mark weak or estimated city benchmarks as `low` or `fallback`.
- Update `MARKET_RESEARCH.md` when benchmark values change.

## Automatic Discovery Rules

Automatic discovery is allowed only through approved/provider-based adapters.

- Local approved feeds are allowed when the data is user-controlled, demo data, or otherwise licensed for use.
- Provider APIs are allowed only when the user supplies credentials and the provider terms allow the intended use.
- Provider adapters must be disabled unless configured.
- Provider adapters must preserve provenance, source listing IDs, discovery run IDs, first/last seen timestamps, and raw payload metadata.
- Provider adapters must not expose API keys in frontend code, logs, tests, docs, or committed config.
- Provider adapters must import incomplete backyard or garage evidence as `needs_manual_review`.
- Discovery must deduplicate exact source URLs and source listing IDs, preserve user notes/status/watchlist/private notes on updates, and flag possible duplicates instead of hiding conflicts.
- Discovery must not fetch consumer listing-site pages unless a source-specific review approves that exact path.
- Placeholder providers such as Apify and Bright Data must remain disabled until a concrete provider contract, source review, and tests exist.

## Claims Policy

The app must never claim that live Zillow, Redfin, Realtor.com, Apartments.com, HotPads, Craigslist, Facebook Marketplace, or any other site scraping works unless that source adapter has been implemented, tested, reviewed, and documented.

Current supported ingestion paths are mock/approved-provider discovery, optional configured RentCast API discovery, browser clipping, manual entry, copy/paste import, CSV import, and URL reference capture.

## Source-Specific Risk Notes

- Zillow terms prohibit automated queries, screen/database scraping, robots, crawlers, and CAPTCHA bypass activity on the services.
- Redfin terms prohibit automated crawling/querying and scraping without express written permission.
- Realtor.com terms prohibit scraping and derivative reuse of Move Network content without express written permission.
- Craigslist terms prohibit collection through robots, spiders, scripts, scrapers, crawlers, or equivalent techniques without a license.
- Apartments.com terms restrict reuse of site materials outside personal/noncommercial use without prior written consent.
- Meta automated data collection terms require express written permission for automated data collection from Meta products.

## References

- Zillow Terms of Use: <https://www.zillow.com/z/corp/terms/>
- Redfin Terms of Use: <https://www.redfin.com/about/terms-of-use>
- Realtor.com Terms of Use: <https://www.realtor.com/terms-of-service/>
- Craigslist Terms of Use: <https://www.craigslist.org/about/terms.html>
- Apartments.com Terms of Service: <https://www.apartments.com/about/terms-of-service>
- Meta Automated Data Collection Terms: <https://www.facebook.com/legal/automated_data_collection_terms>
