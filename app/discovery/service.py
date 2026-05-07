"""Discovery service boundary.

FastAPI routes use `app.services.discovery`; this module exists so provider
authors can discover the package-level service entry points without importing
route code.
"""

from app.services.discovery import (
    get_discovery_provider_run,
    get_discovery_providers,
    get_discovery_runs,
    run_listing_discovery,
)

__all__ = [
    "get_discovery_provider_run",
    "get_discovery_providers",
    "get_discovery_runs",
    "run_listing_discovery",
]
