"""Discovery database models.

The SQLAlchemy models live in `app.models` to keep the MVP metadata schema in
one place. This module gives the discovery package an explicit model boundary.
"""

from app.models import DiscoveryProvider, DiscoveryRun

__all__ = ["DiscoveryProvider", "DiscoveryRun"]
