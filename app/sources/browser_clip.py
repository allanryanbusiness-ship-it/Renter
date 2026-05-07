from __future__ import annotations

from app.schemas import BrowserClipRequest, PasteImportRequest
from app.sources.base import IngestionResult, NormalizedListing, Provenance, confidence_for_source
from app.sources.paste_import import PasteImportAdapter
from app.sources.sanitizer import sanitize_clipped_text
from app.sources.source_inference import infer_source_from_url, normalize_domain


class BrowserClipAdapter:
    source_name = "Browser Clip"
    source_type = "browser_clip"
    enabled_by_default = True

    def ingest(self, payload: BrowserClipRequest) -> IngestionResult:
        source_url = str(payload.source_url)
        source_domain = normalize_domain(payload.source_domain or source_url)
        source_name = infer_source_from_url(source_url) or "Other"
        page_title = sanitize_clipped_text(payload.page_title, max_length=500)
        selected_text = sanitize_clipped_text(payload.selected_text, max_length=20_000)
        page_text = sanitize_clipped_text(payload.page_text, max_length=30_000)
        notes = sanitize_clipped_text(payload.user_notes, max_length=2_000)
        text_parts = [part for part in [selected_text, page_text, page_title] if part]
        combined_text = "\n".join(text_parts)
        warnings: list[str] = []

        if not combined_text:
            combined_text = page_title or source_url
            warnings.append("No selected or page text was captured; saved as URL reference for manual review.")

        paste_result = PasteImportAdapter().ingest(
            PasteImportRequest(
                raw_text=combined_text,
                source_name=source_name,
                source_url=source_url,
                notes=notes,
            )
        )

        if paste_result.listings:
            listing = paste_result.listings[0]
            if page_title:
                listing.title = page_title[:180]
            listing.provenance.source_type = self.source_type
            listing.provenance.source_domain = source_domain
            listing.provenance.source_confidence = min(listing.provenance.source_confidence, confidence_for_source(self.source_type))
            listing.provenance.raw_text = combined_text
            listing.provenance.raw_payload_json = {
                **listing.provenance.raw_payload_json,
                "clip": {
                    "page_title": page_title,
                    "selected_text": selected_text,
                    "page_text_captured": bool(page_text),
                    "source_domain": source_domain,
                    "captured_at": payload.captured_at.isoformat() if payload.captured_at else None,
                },
            }
            listing.feature_tags = list(dict.fromkeys(listing.feature_tags + ["browser_clip"]))
            return IngestionResult(listings=[listing], rows_received=1, rows_imported=1, warnings=warnings)

        warnings.extend(error["message"] for error in paste_result.errors)
        fallback_listing = NormalizedListing(
            title=page_title or f"{source_name} clipped listing",
            city="Unknown",
            price_monthly=0,
            bedrooms=0,
            bathrooms=0,
            description=combined_text[:500],
            listing_status="needs_manual_review",
            watchlist_status="needs_manual_review",
            notes=notes,
            feature_tags=["browser_clip", "needs_manual_review"],
            provenance=Provenance(
                source_name=source_name,
                source_type=self.source_type,
                source_url=source_url,
                source_domain=source_domain,
                source_confidence=confidence_for_source(self.source_type, 0.55),
                raw_text=combined_text,
                raw_payload_json={
                    "clip": {
                        "page_title": page_title,
                        "selected_text": selected_text,
                        "page_text_captured": bool(page_text),
                        "source_domain": source_domain,
                        "captured_at": payload.captured_at.isoformat() if payload.captured_at else None,
                    },
                    "parser_errors": paste_result.errors,
                },
            ),
        )
        return IngestionResult(listings=[fallback_listing], rows_received=1, rows_imported=1, warnings=warnings)


def extracted_fields_for(listing: NormalizedListing) -> list[str]:
    fields = []
    if listing.price_monthly > 0:
        fields.append("price_monthly")
    if listing.bedrooms > 0:
        fields.append("bedrooms")
    if listing.bathrooms > 0:
        fields.append("bathrooms")
    if listing.square_feet:
        fields.append("square_feet")
    if listing.address:
        fields.append("address")
    if listing.city and listing.city != "Unknown":
        fields.append("city")
    if listing.state:
        fields.append("state")
    if listing.zip:
        fields.append("zip")
    if listing.backyard_status != "unknown":
        fields.append("backyard_status")
    if listing.garage_status != "unknown":
        fields.append("garage_status")
    if listing.parking_details:
        fields.append("parking_details")
    if listing.pet_policy:
        fields.append("pet_policy")
    if listing.laundry:
        fields.append("laundry")
    if listing.air_conditioning:
        fields.append("air_conditioning")
    return fields
