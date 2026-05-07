"""Automatic listing discovery package."""

from app.discovery.adapters import (
    ApifyPlaceholderAdapter,
    ApprovedProviderFeedAdapter,
    BrightDataPlaceholderAdapter,
    ListingDiscoveryAdapter,
    ListingDiscoveryCriteria,
    MockDiscoveryProviderAdapter,
    RentCastRentalListingsAdapter,
    discovery_adapter_registry,
    list_discovery_provider_info,
)
from app.discovery.base import DiscoveryProviderAdapter

__all__ = [
    "ApifyPlaceholderAdapter",
    "ApprovedProviderFeedAdapter",
    "BrightDataPlaceholderAdapter",
    "DiscoveryProviderAdapter",
    "ListingDiscoveryAdapter",
    "ListingDiscoveryCriteria",
    "MockDiscoveryProviderAdapter",
    "RentCastRentalListingsAdapter",
    "discovery_adapter_registry",
    "list_discovery_provider_info",
]
