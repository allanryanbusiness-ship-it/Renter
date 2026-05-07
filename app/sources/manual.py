from __future__ import annotations

from app.schemas import ManualListingCreate
from app.sources.base import IngestionResult, NormalizedListing, Provenance, confidence_for_source, normalize_status


class ManualEntryAdapter:
    source_name = "Manual Import"
    source_type = "manual"
    enabled_by_default = True

    def ingest(self, payload: ManualListingCreate) -> IngestionResult:
        backyard_status = normalize_status(payload.backyard_status) if payload.backyard_status else ("yes" if payload.has_backyard else "no")
        garage_status = normalize_status(payload.garage_status) if payload.garage_status else ("yes" if payload.has_garage else "no")
        source_name = payload.source_name or self.source_name
        source_url = str(payload.listing_url) if payload.listing_url else None
        raw_payload = payload.model_dump(mode="json")
        confidence = confidence_for_source(self.source_type)

        listing = NormalizedListing(
            title=payload.title,
            address=payload.address_line1,
            city=payload.city,
            neighborhood=payload.neighborhood,
            county=payload.county,
            state=payload.state,
            zip=payload.postal_code,
            price_monthly=float(payload.price),
            bedrooms=payload.bedrooms,
            bathrooms=payload.bathrooms,
            square_feet=payload.square_feet,
            lot_size=payload.lot_size_sqft,
            property_type=payload.property_type,
            backyard_status=backyard_status,
            backyard_evidence=payload.backyard_evidence,
            garage_status=garage_status,
            garage_evidence=payload.garage_evidence,
            parking_details=payload.parking_details,
            pet_policy=payload.pet_policy,
            laundry=payload.laundry,
            air_conditioning=payload.air_conditioning,
            watchlist_status=payload.watchlist_status,
            notes=payload.note,
            description=payload.description,
            feature_tags=[
                tag
                for tag, enabled in {
                    "backyard": backyard_status == "yes",
                    "garage": garage_status == "yes",
                    "pets": payload.pets_allowed is True,
                    "manual": True,
                }.items()
                if enabled
            ],
            provenance=Provenance(
                source_name=source_name,
                source_type=self.source_type,
                source_url=source_url,
                source_confidence=confidence,
                raw_payload_json=raw_payload,
            ),
        )
        return IngestionResult(listings=[listing], rows_received=1, rows_imported=1)

