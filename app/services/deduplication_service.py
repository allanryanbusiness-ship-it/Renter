"""Deduplication helpers for listing ingestion.

The implementation remains in `app.services.listings` because manual, clip,
CSV, and discovery imports share one persistence path. This module documents the
matching strategy for future provider work.
"""

DEDUPLICATION_RULES = [
    "exact source URL",
    "source listing ID",
    "normalized address",
    "title + city + price",
    "address + price",
    "possible duplicate warning when uncertain",
]

__all__ = ["DEDUPLICATION_RULES"]
