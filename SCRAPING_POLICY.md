# Scraping Policy

## Intent

This project is designed to support lawful, transparent, and low-risk data collection for rental comparison workflows.

## Rules

- Respect each site's terms of use, robots directives, and rate limits.
- Do not add credential theft, CAPTCHA evasion, anti-bot bypass, or deceptive browser automation.
- Do not ship stealth proxy-rotation or fingerprint-spoofing workflows.
- Keep high-risk adapters disabled by default unless a compliant approval path exists.
- Prefer manual entry, CSV import, feed partnerships, licensed APIs, and public datasets.

## Source-Specific Risk Notes

- Craigslist terms prohibit collecting content through robots, spiders, scripts, scrapers, crawlers, or manual equivalents.
- Realtor.com terms prohibit scraping and derivative reuse of its content without express written permission.
- Redfin terms prohibit scraping, data mining, and related collection activity.
- Zillow access should be treated as partner- or license-based unless the user supplies an approved data path.

## Approved MVP Paths

- Seed/demo data
- User-provided manual listing URLs
- User-pasted listing details
- CSV imports from user-controlled exports
- Public market datasets such as HUD and Census
- Licensed APIs added through explicit adapters

## References

- Craigslist Terms of Use: <https://www.craigslist.org/about/terms>
- Realtor.com Terms of Use: <https://www.realtor.com/terms-of-service/>
- Redfin Terms of Use: <https://www.redfin.com/about/terms-of-use>
- Zillow Terms of Use: <https://www.zillow.com/corporate/terms-of-use/>

