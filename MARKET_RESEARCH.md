# Market Research

Research date: 2026-05-06

Scope: Orange County, California rental benchmarks for the dashboard's target search: at least 3 bedrooms, backyard required, garage required.

## Method

The benchmark file uses public, manually reviewed source pages. No app code scrapes, crawls, bypasses CAPTCHA, uses proxies, or fetches listing pages in the background.

Primary city inputs came from public Apartments.com rent trend pages because they publish city-level floor-plan rent and average-square-foot figures. These figures are apartment-oriented averages, not guaranteed medians for detached homes with backyards and garages. HUD/FMR sources are used only as county/fair-market context, not as private-market asking-rent truth.

## Sources Used

- Apartments.com rent trend pages for Irvine, Costa Mesa, Huntington Beach, Newport Beach, Orange, Anaheim, Tustin, Fullerton, Mission Viejo, Lake Forest, Garden Grove, Santa Ana, Aliso Viejo, Laguna Niguel, and Yorba Linda: <https://www.apartments.com/rent-market-trends/>
- HUD USER Fair Market Rents landing page: <https://www.huduser.gov/portal/datasets/fmr.html>
- fmr.fyi Santa Ana FY2026 HUD/SAFMR view: <https://fmr.fyi/city/santa-ana-ca>

Apartments.com pages state that their rent data is provided by CoStar Group market trend reports and show May 2026 values on the pages reviewed.

## Benchmark Table

| City | 3BR Benchmark | Typical Low | Typical High | $/Sqft Benchmark | Confidence | Primary Source |
|---|---:|---:|---:|---:|---|---|
| Irvine | $4,386 | $3,800 | $5,500 | $3.35 | medium | Apartments.com Irvine rent trends |
| Costa Mesa | $3,359 | $2,900 | $4,400 | $2.92 | medium | Apartments.com Costa Mesa rent trends |
| Huntington Beach | $4,131 | $3,500 | $5,400 | $3.21 | medium | Apartments.com Huntington Beach rent trends |
| Newport Beach | $5,700 | $4,800 | $7,600 | $3.96 | medium | Apartments.com Newport Beach rent trends |
| Orange | $3,700 | $3,200 | $4,800 | $2.82 | medium | Apartments.com Orange rent trends |
| Anaheim | $2,988 | $2,600 | $3,900 | $2.66 | medium | Apartments.com Anaheim rent trends |
| Tustin | $3,598 | $3,100 | $4,700 | $2.78 | medium | Apartments.com Tustin rent trends |
| Fullerton | $3,572 | $3,100 | $4,600 | $2.89 | medium | Apartments.com Fullerton rent trends |
| Mission Viejo | $3,924 | $3,400 | $5,300 | $3.13 | low | Apartments.com Mission Viejo rent trends |
| Lake Forest | $3,970 | $3,400 | $5,300 | $2.98 | low | Apartments.com Lake Forest rent trends |
| Garden Grove | $2,703 | $2,350 | $3,600 | $2.58 | medium | Apartments.com Garden Grove rent trends |
| Santa Ana | $3,248 | $2,800 | $4,300 | $2.64 | medium | Apartments.com Santa Ana rent trends; fmr.fyi cross-check |
| Aliso Viejo | $4,472 | $3,800 | $6,000 | $2.55 | low | Apartments.com Aliso Viejo rent trends |
| Laguna Niguel | $3,878 | $3,350 | $5,200 | $2.99 | low | Apartments.com Laguna Niguel rent trends |
| Yorba Linda | $3,933 | $3,400 | $5,300 | $2.71 | low | Apartments.com Yorba Linda rent trends |
| Orange County fallback | $3,900 | $3,250 | $4,500 | $2.89 | fallback | Synthesis of researched cities plus HUD/FMR context |

## City Notes

Irvine, Anaheim, Tustin, Fullerton, Santa Ana, Huntington Beach, Costa Mesa, Orange, and Newport Beach are marked medium-confidence because the public city pages had directly published 3-bedroom rent and average-size values. They are still not high-confidence for the target use case because the user is often comparing houses or townhomes with a backyard and garage.

Mission Viejo, Lake Forest, Aliso Viejo, Laguna Niguel, and Yorba Linda are marked low-confidence because 3-bedroom inventory appears more dependent on houses/townhomes and smaller comparable sets. Treat below-market signals there as prompts for manual verification, not as final deal conclusions.

Newport Beach and coastal Huntington Beach have especially broad rent dispersion. A listing can be above the apartment benchmark and still be reasonable if it is a detached house, larger, remodeled, coastal, or has unusually strong parking/outdoor-space features.

Garden Grove and Anaheim benchmarks can make some family-sized listings look expensive if the listing is a detached home rather than an apartment. Use source URL, backyard evidence, garage evidence, and neighborhood context before rejecting.

## How Benchmarks Are Used

The app compares a listing against its city benchmark when available. It computes:

- rent delta versus the 3-bedroom benchmark
- rent delta percent
- market label: `below_typical_low`, `below_market`, `near_market`, or `above_typical_high`
- price-per-square-foot delta when square footage exists
- low-confidence or fallback warnings

If no city benchmark exists, the app uses the `Orange County` fallback and lowers confidence.

## How To Update Later

1. Review current public sources or approved data providers.
2. Edit [app/data/city_benchmarks.json](app/data/city_benchmarks.json).
3. Preserve `data_sources`, `accessed_at`, confidence, and notes.
4. Run `uv run pytest`.
5. If scoring behavior changes, update the market research notes and score tests.

## Limitations

- Apartments.com city trend data is apartment-oriented and may not represent detached houses.
- The app target requires backyard and garage, which can add a premium not captured in simple 3-bedroom averages.
- Public listing-summary pages can change quickly.
- HUD/FMR data is useful policy context but is not the same as current private-market asking rent.
- Benchmark values should be treated as editable assumptions, not ground truth.
