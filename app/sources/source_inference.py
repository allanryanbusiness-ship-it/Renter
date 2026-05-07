from __future__ import annotations

from urllib.parse import urlparse


DOMAIN_SOURCE_MAP = {
    "zillow.com": "Zillow",
    "redfin.com": "Redfin",
    "realtor.com": "Realtor",
    "apartments.com": "Apartments.com",
    "hotpads.com": "HotPads",
    "craigslist.org": "Craigslist",
    "facebook.com": "Facebook Marketplace",
    "fb.com": "Facebook Marketplace",
}

PROPERTY_MANAGER_TERMS = (
    "propertymanagement",
    "property-management",
    "rentals",
    "rent",
    "leasing",
    "management",
    "apartments",
)


def normalize_domain(url_or_domain: str | None) -> str | None:
    if not url_or_domain:
        return None
    value = url_or_domain.strip()
    parsed = urlparse(value if "://" in value else f"https://{value}")
    hostname = (parsed.hostname or "").lower()
    if hostname.startswith("www."):
        hostname = hostname[4:]
    return hostname or None


def infer_source_from_url(url: str | None) -> str | None:
    domain = normalize_domain(url)
    if not domain:
        return None
    for mapped_domain, source in DOMAIN_SOURCE_MAP.items():
        if domain == mapped_domain or domain.endswith(f".{mapped_domain}"):
            return source
    if any(term in domain for term in PROPERTY_MANAGER_TERMS):
        return "Property Management Site"
    return "Other"

