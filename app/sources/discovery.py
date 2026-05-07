from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen

from app.config import (
    APPROVED_PROVIDER_FEED_PATH,
    APPROVED_PROVIDER_API_KEY,
    APPROVED_PROVIDER_API_NAME,
    APPROVED_PROVIDER_API_TIMEOUT_SECONDS,
    APPROVED_PROVIDER_API_URL,
    DISCOVERY_DEFAULT_CITIES,
    ORANGE_COUNTY_DISCOVERY_CITIES,
)
from app.sources.base import IngestionResult, NormalizedListing, Provenance, confidence_for_source, normalize_status
from app.sources.normalizer import OC_CITIES, clean_text, find_evidence, parse_float, parse_int, parse_money


@dataclass(slots=True)
class ListingDiscoveryCriteria:
    county: str = "Orange County"
    state: str = "CA"
    city: str | None = None
    preferred_cities: list[str] | None = None
    zip_codes: list[str] | None = None
    min_bedrooms: int = 3
    min_bathrooms: float = 2.0
    max_price: int | None = 6500
    min_sqft: int | None = 1400
    require_backyard: bool = True
    require_garage: bool = True
    allow_unknown_backyard: bool = True
    allow_unknown_garage: bool = True
    pets_required: bool = False
    property_types: list[str] | None = None
    provider_names: list[str] | None = None
    limit: int = 25


@dataclass(frozen=True, slots=True)
class DiscoveryProviderInfo:
    key: str
    source_name: str
    source_type: str
    provider_name: str
    provider_type: str
    status: str
    is_enabled: bool
    enabled_by_default: bool
    configured: bool
    requires_api_key: bool
    supported_locations: list[str]
    supports_rentals: bool
    supports_filters: list[str]
    docs_url: str | None
    rate_limit_notes: str
    compliance_notes: str


class ListingDiscoveryAdapter(Protocol):
    key: str
    source_name: str
    source_type: str
    provider_name: str
    provider_type: str
    enabled_by_default: bool
    requires_api_key: bool
    supported_locations: list[str]
    supports_rentals: bool
    supports_filters: list[str]
    docs_url: str | None
    rate_limit_notes: str
    compliance_notes: str

    @property
    def configured(self) -> bool:
        ...

    @property
    def is_enabled(self) -> bool:
        ...

    def search(self, criteria: ListingDiscoveryCriteria) -> IngestionResult:
        ...

    def normalize(self, raw_listing: dict[str, Any], criteria: ListingDiscoveryCriteria | None = None) -> NormalizedListing | None:
        ...

    def validate_config(self) -> bool:
        ...

    def discover(self, criteria: ListingDiscoveryCriteria) -> IngestionResult:
        ...

    def metadata(self) -> DiscoveryProviderInfo:
        ...


class ProviderConfigurationError(RuntimeError):
    pass


class BaseDiscoveryAdapter:
    key = ""
    source_name = ""
    source_type = "provider_feed"
    enabled_by_default = False
    requires_api_key = False
    docs_url: str | None = None
    supported_locations: list[str] = ORANGE_COUNTY_DISCOVERY_CITIES
    supports_rentals = True
    supports_filters = [
        "city",
        "state",
        "zip_code",
        "min_bedrooms",
        "min_bathrooms",
        "max_price",
        "min_sqft",
        "backyard",
        "garage",
        "pets",
        "property_type",
    ]
    rate_limit_notes = "No external request is made by the base adapter."
    compliance_notes = ""

    @property
    def provider_name(self) -> str:
        return self.source_name

    @property
    def provider_type(self) -> str:
        return self.source_type

    @property
    def configured(self) -> bool:
        return True

    @property
    def is_enabled(self) -> bool:
        return self.configured

    @property
    def status(self) -> str:
        if self.enabled_by_default and self.configured:
            return "active"
        if self.configured:
            return "available"
        return "not_configured"

    def metadata(self) -> DiscoveryProviderInfo:
        return DiscoveryProviderInfo(
            key=self.key,
            source_name=self.source_name,
            source_type=self.source_type,
            provider_name=self.provider_name,
            provider_type=self.provider_type,
            status=self.status,
            is_enabled=self.is_enabled,
            enabled_by_default=self.enabled_by_default,
            configured=self.configured,
            requires_api_key=self.requires_api_key,
            supported_locations=list(self.supported_locations),
            supports_rentals=self.supports_rentals,
            supports_filters=list(self.supports_filters),
            docs_url=self.docs_url,
            rate_limit_notes=self.rate_limit_notes,
            compliance_notes=self.compliance_notes,
        )

    def search(self, criteria: ListingDiscoveryCriteria) -> IngestionResult:
        return self.discover(criteria)

    def normalize(self, raw_listing: dict[str, Any], criteria: ListingDiscoveryCriteria | None = None) -> NormalizedListing | None:
        return _record_to_normalized_listing(
            raw_listing,
            criteria or ListingDiscoveryCriteria(),
            source_name=self.source_name,
            source_type=self.source_type,
            source_domain=None,
            raw_payload_prefix={"provider": self.key},
        )

    def validate_config(self) -> bool:
        if not self.configured:
            raise ProviderConfigurationError(f"{self.source_name} is not configured.")
        return True


class ApprovedProviderFeedAdapter(BaseDiscoveryAdapter):
    key = "approved_demo_feed"
    source_name = "Approved Demo Provider Feed"
    source_type = "provider_feed"
    enabled_by_default = True
    requires_api_key = False
    docs_url = "AUTOMATIC_LISTING_DISCOVERY.md"
    rate_limit_notes = "Local JSON feed; no network calls or provider rate limits."
    compliance_notes = "Local provider-style feed. No external page fetches, scraping, CAPTCHA bypass, or proxy use."

    def __init__(self, feed_path: Path = APPROVED_PROVIDER_FEED_PATH) -> None:
        self.feed_path = feed_path

    @property
    def configured(self) -> bool:
        return self.feed_path.exists()

    def discover(self, criteria: ListingDiscoveryCriteria) -> IngestionResult:
        if not self.configured:
            raise ProviderConfigurationError(f"Approved provider feed not found: {self.feed_path}")

        payload = json.loads(self.feed_path.read_text())
        raw_listings = payload.get("listings", [])
        result = IngestionResult(rows_received=len(raw_listings))
        limit_reached = False

        for record in raw_listings:
            listing = _record_to_normalized_listing(
                record,
                criteria,
                source_name=self.source_name,
                source_type=self.source_type,
                source_domain="example.com",
                raw_payload_prefix={"feed_path": str(self.feed_path), "feed_meta": payload.get("_meta", {})},
            )
            if listing is None:
                result.rows_skipped += 1
                continue
            if len(result.listings) >= criteria.limit:
                result.rows_skipped += 1
                limit_reached = True
                continue
            result.listings.append(listing)

        result.rows_imported = len(result.listings)
        if limit_reached:
            result.warnings.append(f"Discovery limit of {criteria.limit} candidates was reached.")
        if not result.listings:
            result.warnings.append("No provider-feed candidates matched the active search criteria.")
        return result


class MockDiscoveryProviderAdapter(ApprovedProviderFeedAdapter):
    key = "mock"
    source_name = "Mock Discovery Provider"
    source_type = "mock_provider"
    enabled_by_default = False
    requires_api_key = False
    docs_url = "AUTOMATIC_LISTING_DISCOVERY.md"
    rate_limit_notes = "Local demo feed; no network calls or rate limits."
    compliance_notes = "Demo/mock data for exercising discovery, dedupe, scoring, and review flows without credentials."


class ApprovedJsonApiAdapter(BaseDiscoveryAdapter):
    key = "approved_json_api"
    source_name = "Approved JSON Provider API"
    source_type = "provider_api"
    enabled_by_default = False
    requires_api_key = False
    docs_url = "DISCOVERY.md"
    rate_limit_notes = "Uses the configured provider endpoint's documented rate limits. Keep request volume low."
    compliance_notes = "Generic approved JSON API adapter. Configure only for sources the user is allowed to use."

    def __init__(
        self,
        api_url: str = APPROVED_PROVIDER_API_URL,
        api_key: str = APPROVED_PROVIDER_API_KEY,
        provider_name: str = APPROVED_PROVIDER_API_NAME,
        timeout_seconds: float = APPROVED_PROVIDER_API_TIMEOUT_SECONDS,
    ) -> None:
        self.api_url = api_url.strip()
        self.api_key = api_key.strip()
        self.source_name = provider_name or self.source_name
        self.timeout_seconds = timeout_seconds

    @property
    def configured(self) -> bool:
        return bool(self.api_url)

    @property
    def status(self) -> str:
        if self.configured:
            return "available"
        return "not_configured"

    @property
    def is_enabled(self) -> bool:
        return self.configured

    def discover(self, criteria: ListingDiscoveryCriteria) -> IngestionResult:
        if not self.configured:
            raise ProviderConfigurationError(
                "Approved JSON API discovery requires RENTAL_DASHBOARD_PROVIDER_API_URL. "
                "Only configure it for a provider/feed the user is allowed to use."
            )

        records = self._fetch_records(criteria)
        result = IngestionResult()
        result.rows_received = len(records)
        source_domain = urlparse(self.api_url).netloc or None
        limit_reached = False
        for record in records:
            listing = _record_to_normalized_listing(
                record,
                criteria,
                source_name=self.source_name,
                source_type=self.source_type,
                source_domain=source_domain,
                raw_payload_prefix={
                    "provider": self.key,
                    "api_url": self.api_url,
                },
            )
            if listing is None:
                result.rows_skipped += 1
                continue
            if len(result.listings) >= criteria.limit:
                result.rows_skipped += 1
                limit_reached = True
                break
            result.listings.append(listing)

        result.rows_imported = len(result.listings)
        if limit_reached:
            result.warnings.append(f"Discovery limit of {criteria.limit} candidates was reached.")
        if not result.listings:
            result.warnings.append("Approved JSON API returned no candidates matching the active search criteria.")
        return result

    def _fetch_records(self, criteria: ListingDiscoveryCriteria) -> list[dict[str, Any]]:
        query: dict[str, Any] = {
            "state": criteria.state,
            "limit": criteria.limit,
        }
        cities = _cities_for_provider_query(criteria)
        if criteria.city:
            query["city"] = criteria.city
        if cities:
            query["cities"] = ",".join(cities)
        if criteria.zip_codes:
            query["zip_codes"] = ",".join(criteria.zip_codes)
        if criteria.min_bedrooms:
            query["min_bedrooms"] = criteria.min_bedrooms
        if criteria.min_bathrooms:
            query["min_bathrooms"] = criteria.min_bathrooms
        if criteria.min_sqft:
            query["min_sqft"] = criteria.min_sqft
        if criteria.max_price:
            query["max_price"] = criteria.max_price
        if criteria.property_types:
            query["property_types"] = ",".join(criteria.property_types)

        separator = "&" if "?" in self.api_url else "?"
        url = f"{self.api_url}{separator}{urlencode(query)}"
        headers = {
            "Accept": "application/json",
            "User-Agent": "RenterDashboard/0.1 approved-provider-api",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = Request(
            url,
            headers=headers,
            method="GET",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise ProviderConfigurationError(f"Approved JSON API request failed with HTTP {exc.code}.") from exc
        except URLError as exc:
            raise ProviderConfigurationError(f"Approved JSON API request failed: {exc.reason}") from exc

        if isinstance(payload, dict):
            payload = payload.get("listings") or payload.get("results") or payload.get("data")
        if not isinstance(payload, list):
            raise ProviderConfigurationError("Approved JSON API response must be a listing array or object with listings/results/data.")
        return [record for record in payload if isinstance(record, dict)]


class DisabledProviderPlaceholderAdapter(BaseDiscoveryAdapter):
    key = ""
    source_name = ""
    source_type = "provider_placeholder"
    enabled_by_default = False
    requires_api_key = True
    supported_locations = ORANGE_COUNTY_DISCOVERY_CITIES
    supports_rentals = True
    supports_filters = ["source_url", "city", "state", "property_type"]
    rate_limit_notes = "Not implemented. Review provider plan limits before enabling."
    compliance_notes = "Placeholder only. Requires compliance review, explicit configuration, and tests before use."
    env_var_name = ""

    @property
    def configured(self) -> bool:
        return False

    @property
    def status(self) -> str:
        return "not_implemented"

    @property
    def is_enabled(self) -> bool:
        return False

    def discover(self, criteria: ListingDiscoveryCriteria) -> IngestionResult:
        raise ProviderConfigurationError(
            f"{self.source_name} is a disabled placeholder. Configure and implement {self.env_var_name} only after compliance review."
        )

    def validate_config(self) -> bool:
        self.discover(ListingDiscoveryCriteria(limit=1))
        return False


class ApifyPlaceholderAdapter(DisabledProviderPlaceholderAdapter):
    key = "apify"
    source_name = "Apify Placeholder"
    docs_url = "https://apify.com/"
    env_var_name = "APIFY_API_TOKEN"
    compliance_notes = (
        "Disabled placeholder for future approved Apify actor integrations. "
        "Do not enable without source-specific terms review and tests."
    )


class BrightDataPlaceholderAdapter(DisabledProviderPlaceholderAdapter):
    key = "brightdata"
    source_name = "Bright Data Placeholder"
    docs_url = "https://brightdata.com/"
    env_var_name = "BRIGHTDATA_API_KEY"
    compliance_notes = (
        "Disabled placeholder for future Bright Data provider integrations. "
        "Do not enable without source-specific terms review and tests."
    )


def discovery_adapter_registry() -> dict[str, ListingDiscoveryAdapter]:
    return {
        "approved_demo_feed": ApprovedProviderFeedAdapter(),
        "mock": MockDiscoveryProviderAdapter(),
        "approved_json_api": ApprovedJsonApiAdapter(),
        "apify": ApifyPlaceholderAdapter(),
        "brightdata": BrightDataPlaceholderAdapter(),
    }


def list_discovery_provider_info() -> list[DiscoveryProviderInfo]:
    return [adapter.metadata() for adapter in discovery_adapter_registry().values()]


def _record_to_normalized_listing(
    record: dict[str, Any],
    criteria: ListingDiscoveryCriteria,
    *,
    source_name: str,
    source_type: str,
    source_domain: str | None,
    raw_payload_prefix: dict[str, Any],
) -> NormalizedListing | None:
    price = parse_money(_first(record, "price", "rent", "priceMonthly", "monthlyRent", "listPrice"))
    bedrooms = parse_int(_first(record, "bedrooms", "beds"))
    bathrooms = parse_float(_first(record, "bathrooms", "baths"))
    square_feet = parse_int(_first(record, "squareFootage", "square_feet", "sqft", "livingArea"))
    city = clean_text(_first(record, "city", "locality")) or "Unknown"
    county = clean_text(_first(record, "county")) or criteria.county or "Orange County"
    state = clean_text(_first(record, "state")) or criteria.state or "CA"
    postal_code = clean_text(_first(record, "zipCode", "zip", "postalCode", "postal_code"))
    property_type = clean_text(_first(record, "propertyType", "property_type", "type")) or "unknown"
    backyard_status, backyard_evidence = _feature_status(
        record,
        status_keys=("backyardStatus", "backyard_status", "yardStatus", "yard_status"),
        bool_keys=("hasBackyard", "has_backyard", "backyard", "yard"),
        evidence_keys=("backyardEvidence", "backyard_evidence", "yardEvidence", "yard_evidence"),
        positive_terms=("backyard", "back yard", "private yard", "fenced yard", "patio yard", "enclosed patio"),
        negative_terms=("no backyard", "no yard", "shared courtyard only"),
    )
    garage_status, garage_evidence = _feature_status(
        record,
        status_keys=("garageStatus", "garage_status", "parkingGarageStatus"),
        bool_keys=("hasGarage", "has_garage", "garage"),
        evidence_keys=("garageEvidence", "garage_evidence", "parkingGarageEvidence"),
        positive_terms=("garage", "attached garage", "two-car garage", "2 car garage", "direct-access garage"),
        negative_terms=("no garage", "street parking only"),
    )

    if price is None or bedrooms is None or bathrooms is None:
        return None
    if not _matches_criteria(
        city=city,
        county=county,
        state=state,
        price=price,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        square_feet=square_feet,
        postal_code=postal_code,
        property_type=property_type,
        backyard_status=backyard_status,
        garage_status=garage_status,
        pet_policy=clean_text(_first(record, "pets", "petPolicy", "pet_policy")),
        criteria=criteria,
    ):
        return None

    source_listing_id = clean_text(_first(record, "id", "listingId", "listing_id", "sourceListingId", "mlsNumber"))
    source_url = clean_text(_first(record, "sourceUrl", "source_url", "listingUrl", "url"))
    if not source_url and source_listing_id:
        source_url = f"https://example.com/approved-provider-feed/{quote(source_listing_id)}"

    raw_text = _raw_text_for_record(record)
    completeness_fields = [
        price,
        bedrooms,
        bathrooms,
        square_feet,
        city if city != "Unknown" else None,
        backyard_status if backyard_status != "unknown" else None,
        garage_status if garage_status != "unknown" else None,
        source_url,
    ]
    completeness = sum(bool(field) for field in completeness_fields) / len(completeness_fields)
    listing_status = "active"
    watchlist_status = "review"
    notes = clean_text(_first(record, "notes", "providerNotes"))
    if (criteria.require_backyard and backyard_status == "unknown") or (criteria.require_garage and garage_status == "unknown"):
        listing_status = "needs_manual_review"
        watchlist_status = "needs_manual_review"
        notes = notes or "Provider discovery imported this candidate with incomplete backyard or garage evidence."

    return NormalizedListing(
        title=clean_text(_first(record, "title", "name")) or f"{city} provider rental candidate",
        description=clean_text(_first(record, "description", "summary", "remarks")),
        address=clean_text(_first(record, "addressLine1", "address_line1", "address", "formattedAddress")),
        city=city,
        county=county,
        state=state,
        zip=postal_code,
        neighborhood=clean_text(_first(record, "neighborhood", "area")),
        latitude=parse_float(_first(record, "latitude", "lat")),
        longitude=parse_float(_first(record, "longitude", "lng", "lon")),
        price_monthly=price,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        square_feet=square_feet,
        lot_size=parse_int(_first(record, "lotSize", "lot_size", "lotSizeSqft", "lot_size_sqft")),
        property_type=property_type,
        backyard_status=backyard_status,
        backyard_evidence=backyard_evidence,
        garage_status=garage_status,
        garage_evidence=garage_evidence,
        parking_details=clean_text(_first(record, "parking", "parkingDetails", "parking_details")),
        pet_policy=clean_text(_first(record, "pets", "petPolicy", "pet_policy")),
        laundry=clean_text(_first(record, "laundry")),
        air_conditioning=clean_text(_first(record, "airConditioning", "air_conditioning", "ac")),
        listing_status=listing_status,
        watchlist_status=watchlist_status,
        notes=notes,
        feature_tags=[
            tag
            for tag, status in {"backyard": backyard_status, "garage": garage_status}.items()
            if status == "yes"
        ]
        + ["automatic_discovery", source_type],
        provenance=Provenance(
            source_name=source_name,
            source_type=source_type,
            source_url=source_url,
            source_domain=source_domain,
            source_listing_id=source_listing_id,
            source_confidence=confidence_for_source(source_type, completeness),
            imported_at=_parse_datetime(_first(record, "lastSeenDate", "last_seen_date", "listedDate", "listed_at")) or datetime.utcnow(),
            raw_text=raw_text,
            raw_payload_json={
                **raw_payload_prefix,
                "source_record": record,
                "automatic_discovery": True,
            },
        ),
    )


def _matches_criteria(
    *,
    city: str,
    county: str,
    state: str,
    price: float,
    bedrooms: int,
    bathrooms: float,
    square_feet: int | None,
    postal_code: str | None,
    property_type: str,
    backyard_status: str,
    garage_status: str,
    pet_policy: str | None,
    criteria: ListingDiscoveryCriteria,
) -> bool:
    if state.upper() != criteria.state.upper():
        return False
    if criteria.county and county.lower() != criteria.county.lower() and city not in OC_CITIES:
        return False
    city_filters = [item.lower() for item in ([criteria.city] if criteria.city else []) + (criteria.preferred_cities or [])]
    if city_filters and city.lower() not in city_filters:
        return False
    zip_filters = {item.strip() for item in (criteria.zip_codes or []) if item and item.strip()}
    if zip_filters and postal_code not in zip_filters:
        return False
    property_filters = {_filter_key(item) for item in (criteria.property_types or []) if item}
    if property_filters and _filter_key(property_type) not in property_filters:
        return False
    if bedrooms < criteria.min_bedrooms:
        return False
    if bathrooms < criteria.min_bathrooms:
        return False
    if criteria.max_price is not None and price > criteria.max_price:
        return False
    if criteria.min_sqft is not None and square_feet is not None and square_feet < criteria.min_sqft:
        return False
    if criteria.require_backyard and backyard_status == "no":
        return False
    if criteria.require_backyard and backyard_status == "unknown" and not criteria.allow_unknown_backyard:
        return False
    if criteria.require_garage and garage_status == "no":
        return False
    if criteria.require_garage and garage_status == "unknown" and not criteria.allow_unknown_garage:
        return False
    if criteria.pets_required and not _allows_pets(pet_policy):
        return False
    return True


def _cities_for_provider_query(criteria: ListingDiscoveryCriteria) -> list[str]:
    cities = []
    if criteria.city:
        cities.append(criteria.city)
    cities.extend(criteria.preferred_cities or [])
    if not cities:
        cities.extend(DISCOVERY_DEFAULT_CITIES)
    return list(dict.fromkeys(city for city in cities if city))


def _first(record: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in record and record[key] not in (None, ""):
            return record[key]
    return None


def _feature_status(
    record: dict[str, Any],
    *,
    status_keys: tuple[str, ...],
    bool_keys: tuple[str, ...],
    evidence_keys: tuple[str, ...],
    positive_terms: tuple[str, ...],
    negative_terms: tuple[str, ...],
) -> tuple[str, str | None]:
    status_value = _first(record, *status_keys)
    if status_value is not None:
        status = normalize_status(str(status_value))
        evidence = clean_text(
            _first(
                record,
                *evidence_keys,
                *(f"{key}Evidence" for key in status_keys),
                *(f"{key}_evidence" for key in status_keys),
            )
        )
        if evidence is None:
            evidence = find_evidence(_raw_text_for_record(record), list(positive_terms + negative_terms))
        return status, evidence

    bool_value = _first(record, *bool_keys)
    if isinstance(bool_value, bool):
        return ("yes" if bool_value else "no"), find_evidence(_raw_text_for_record(record), list(positive_terms + negative_terms))
    if isinstance(bool_value, str):
        status = normalize_status(bool_value)
        if status != "unknown":
            return status, find_evidence(_raw_text_for_record(record), list(positive_terms + negative_terms))

    text = _raw_text_for_record(record)
    lowered = text.lower()
    if any(term in lowered for term in negative_terms):
        return "no", find_evidence(text, list(negative_terms))
    if any(term in lowered for term in positive_terms):
        return "yes", find_evidence(text, list(positive_terms))
    return "unknown", None


def _allows_pets(pet_policy: str | None) -> bool:
    if not pet_policy:
        return False
    lowered = pet_policy.lower()
    if any(term in lowered for term in ("no pets", "not allowed", "not permitted")):
        return False
    return any(term in lowered for term in ("pet", "dog", "cat", "allowed", "considered", "negotiable"))


def _filter_key(value: str | None) -> str:
    return "".join(char for char in (value or "").lower() if char.isalnum())


def _raw_text_for_record(record: dict[str, Any]) -> str:
    values = [
        _first(record, "title", "name"),
        _first(record, "formattedAddress", "address", "addressLine1"),
        _first(record, "city"),
        _first(record, "description", "summary", "remarks"),
        _first(record, "parking", "parkingDetails"),
        _first(record, "pets", "petPolicy"),
        _first(record, "backyardEvidence", "backyard_evidence"),
        _first(record, "garageEvidence", "garage_evidence"),
    ]
    return " ".join(str(value) for value in values if value)


def _parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None
