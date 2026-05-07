"""Provider adapters for automatic listing discovery.

The implementation lives behind this package boundary so discovery can grow
without turning the generic source-ingestion package into an orchestration layer.
"""

from app.sources.discovery import (
    ApifyPlaceholderAdapter,
    ApprovedProviderFeedAdapter,
    BrightDataPlaceholderAdapter,
    DiscoveryProviderInfo,
    DisabledProviderPlaceholderAdapter,
    ListingDiscoveryAdapter,
    ListingDiscoveryCriteria,
    MockDiscoveryProviderAdapter,
    ProviderConfigurationError,
    RentCastRentalListingsAdapter,
    discovery_adapter_registry,
    list_discovery_provider_info,
)

__all__ = [
    "ApifyPlaceholderAdapter",
    "ApprovedProviderFeedAdapter",
    "BrightDataPlaceholderAdapter",
    "DiscoveryProviderInfo",
    "DisabledProviderPlaceholderAdapter",
    "ListingDiscoveryAdapter",
    "ListingDiscoveryCriteria",
    "MockDiscoveryProviderAdapter",
    "ProviderConfigurationError",
    "RentCastRentalListingsAdapter",
    "discovery_adapter_registry",
    "list_discovery_provider_info",
]
