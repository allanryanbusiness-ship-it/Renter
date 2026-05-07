from __future__ import annotations

from app.schemas import UrlReferenceCreate
from app.sources.base import IngestionResult, NormalizedListing, Provenance, confidence_for_source
from app.sources.source_inference import infer_source_from_url, normalize_domain


class UrlReferenceAdapter:
    source_name = "URL Reference"
    source_type = "url_reference"
    enabled_by_default = True

    def ingest(self, payload: UrlReferenceCreate) -> IngestionResult:
        source_url = str(payload.url)
        source_name = payload.source_name or infer_source_from_url(source_url) or self.source_name
        title = payload.title or f"{source_name} listing reference"
        listing = NormalizedListing(
            title=title,
            city="Unknown",
            price_monthly=0,
            bedrooms=0,
            bathrooms=0,
            listing_status="needs_manual_review",
            watchlist_status="needs_manual_review",
            notes=payload.notes,
            feature_tags=["url_reference", "needs_manual_review"],
            provenance=Provenance(
                source_name=source_name,
                source_type=self.source_type,
                source_url=source_url,
                source_domain=normalize_domain(source_url),
                source_confidence=confidence_for_source(self.source_type),
                raw_payload_json={"url_reference_only": True},
            ),
        )
        return IngestionResult(listings=[listing], rows_received=1, rows_imported=1)
