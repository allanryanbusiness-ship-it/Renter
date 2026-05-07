"""Automatic listing discovery package."""

from app.discovery.adapters import (
    ApifyPlaceholderAdapter,
    ApprovedJsonApiAdapter,
    ApprovedProviderFeedAdapter,
    BrightDataPlaceholderAdapter,
    ListingDiscoveryAdapter,
    ListingDiscoveryCriteria,
    MockDiscoveryProviderAdapter,
    discovery_adapter_registry,
    list_discovery_provider_info,
)
from app.discovery.base import DiscoveryProviderAdapter

__all__ = [
    "ApifyPlaceholderAdapter",
    "ApprovedJsonApiAdapter",
    "ApprovedProviderFeedAdapter",
    "BrightDataPlaceholderAdapter",
    "DiscoveryProviderAdapter",
    "ListingDiscoveryAdapter",
    "ListingDiscoveryCriteria",
    "MockDiscoveryProviderAdapter",
    "discovery_adapter_registry",
    "list_discovery_provider_info",
]
