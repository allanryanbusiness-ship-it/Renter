from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol


TRI_STATE_VALUES = {"yes", "no", "unknown"}


@dataclass(slots=True)
class Provenance:
    source_name: str
    source_type: str
    source_url: str | None = None
    source_domain: str | None = None
    source_listing_id: str | None = None
    source_confidence: float = 0.7
    imported_at: datetime = field(default_factory=datetime.utcnow)
    raw_text: str | None = None
    raw_payload_json: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class NormalizedListing:
    title: str
    city: str
    price_monthly: float
    bedrooms: int
    bathrooms: float
    provenance: Provenance
    description: str | None = None
    address: str | None = None
    county: str = "Orange County"
    state: str = "CA"
    zip: str | None = None
    neighborhood: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    square_feet: int | None = None
    lot_size: int | None = None
    property_type: str = "unknown"
    backyard_status: str = "unknown"
    backyard_evidence: str | None = None
    garage_status: str = "unknown"
    garage_evidence: str | None = None
    parking_details: str | None = None
    pet_policy: str | None = None
    laundry: str | None = None
    air_conditioning: str | None = None
    listing_status: str = "active"
    watchlist_status: str = "review"
    notes: str | None = None
    feature_tags: list[str] = field(default_factory=list)


@dataclass(slots=True)
class IngestionResult:
    listings: list[NormalizedListing] = field(default_factory=list)
    rows_received: int = 0
    rows_imported: int = 0
    rows_skipped: int = 0
    errors: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class SourceAdapter(Protocol):
    source_name: str
    source_type: str
    enabled_by_default: bool

    def ingest(self, payload: Any) -> IngestionResult:
        ...


def normalize_status(value: str | None, *, default: str = "unknown") -> str:
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"true", "y", "yes", "confirmed", "available"}:
        return "yes"
    if normalized in {"false", "n", "no", "none", "not available"}:
        return "no"
    if normalized in TRI_STATE_VALUES:
        return normalized
    return default


def confidence_for_source(source_type: str, completeness: float = 1.0) -> float:
    base = {
        "manual": 0.92,
        "paste": 0.68,
        "csv": 0.78,
        "browser_clip": 0.72,
        "url_reference": 0.42,
        "provider_feed": 0.84,
        "provider_api": 0.88,
        "mock_provider": 0.82,
        "approved_provider": 0.86,
        "licensed_api": 0.9,
        "experimental_scraper": 0.35,
    }.get(source_type, 0.6)
    return max(0.05, min(0.99, round(base * completeness, 2)))
