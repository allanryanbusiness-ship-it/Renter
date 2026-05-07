from __future__ import annotations

from typing import Any, Protocol

from app.sources.base import IngestionResult, NormalizedListing


class DiscoveryProviderAdapter(Protocol):
    """Provider interface for approved automatic rental listing discovery."""

    key: str
    provider_name: str
    provider_type: str
    source_name: str
    source_type: str
    is_enabled: bool
    requires_api_key: bool
    supported_locations: list[str]
    supports_rentals: bool
    supports_filters: list[str]
    rate_limit_notes: str
    compliance_notes: str

    def validate_config(self) -> bool:
        """Return true when the provider can be called safely in this environment."""

    def search(self, criteria: Any) -> IngestionResult:
        """Run provider discovery for the supplied saved-search criteria."""

    def normalize(self, raw_listing: dict[str, Any], criteria: Any | None = None) -> NormalizedListing | None:
        """Normalize a provider record into the app's canonical listing schema."""
