"""Approved/provider-based discovery adapters.

Placeholder providers are intentionally disabled until a reviewed configuration
and provider-specific tests exist.
"""

from app.discovery.providers.apify_placeholder import ApifyPlaceholderAdapter
from app.discovery.providers.approved_json_api import ApprovedJsonApiAdapter
from app.discovery.providers.brightdata_placeholder import BrightDataPlaceholderAdapter
from app.discovery.providers.mock_provider import MockDiscoveryProviderAdapter

__all__ = [
    "ApifyPlaceholderAdapter",
    "ApprovedJsonApiAdapter",
    "BrightDataPlaceholderAdapter",
    "MockDiscoveryProviderAdapter",
]
