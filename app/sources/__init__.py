"""Safe ingestion adapters for rental listing sources."""

from app.sources.base import IngestionResult, NormalizedListing, Provenance
from app.sources.browser_clip import BrowserClipAdapter
from app.sources.csv_import import CsvImportAdapter
from app.sources.discovery import ApprovedProviderFeedAdapter, RentCastRentalListingsAdapter
from app.sources.manual import ManualEntryAdapter
from app.sources.paste_import import PasteImportAdapter
from app.sources.source_inference import infer_source_from_url, normalize_domain
from app.sources.url_reference import UrlReferenceAdapter

__all__ = [
    "CsvImportAdapter",
    "ApprovedProviderFeedAdapter",
    "BrowserClipAdapter",
    "IngestionResult",
    "ManualEntryAdapter",
    "NormalizedListing",
    "PasteImportAdapter",
    "Provenance",
    "RentCastRentalListingsAdapter",
    "UrlReferenceAdapter",
    "infer_source_from_url",
    "normalize_domain",
]
