from __future__ import annotations

import csv
from io import StringIO
from typing import Any

from app.schemas import CsvImportRequest
from app.sources.base import IngestionResult, NormalizedListing, Provenance, confidence_for_source, normalize_status
from app.sources.normalizer import bool_from_text, clean_text, parse_float, parse_int, parse_money


FIELD_ALIASES = {
    "title": {"title", "name", "listing_title"},
    "description": {"description", "details", "summary"},
    "address": {"address", "street", "address_line1", "street_address"},
    "city": {"city", "locality"},
    "county": {"county"},
    "state": {"state", "st"},
    "zip": {"zip", "zipcode", "postal_code", "postal"},
    "neighborhood": {"neighborhood", "area"},
    "price_monthly": {"price", "rent", "monthly_rent", "price_monthly", "list_price"},
    "bedrooms": {"bedrooms", "beds", "bd", "br"},
    "bathrooms": {"bathrooms", "baths", "ba"},
    "square_feet": {"square_feet", "sqft", "sq_ft", "living_area"},
    "lot_size": {"lot_size", "lot_size_sqft", "lot_sqft"},
    "property_type": {"property_type", "type"},
    "backyard_status": {"backyard_status", "backyard", "yard"},
    "garage_status": {"garage_status", "garage"},
    "parking_details": {"parking", "parking_details"},
    "pet_policy": {"pets", "pet_policy", "pets_allowed"},
    "source_url": {"url", "listing_url", "source_url"},
    "source_listing_id": {"source_listing_id", "external_id", "listing_id"},
    "notes": {"notes", "note"},
}


def canonical_column(name: str) -> str | None:
    normalized = name.strip().lower().replace(" ", "_").replace("-", "_")
    for canonical, aliases in FIELD_ALIASES.items():
        if normalized in aliases:
            return canonical
    return None


class CsvImportAdapter:
    source_name = "CSV Import"
    source_type = "csv"
    enabled_by_default = True

    def ingest(self, payload: CsvImportRequest) -> IngestionResult:
        reader = csv.DictReader(StringIO(payload.csv_text))
        if not reader.fieldnames:
            return IngestionResult(errors=[{"row_number": None, "message": "CSV header row is required."}])

        result = IngestionResult()
        for row_number, row in enumerate(reader, start=2):
            result.rows_received += 1
            normalized_row, unknown = self._normalize_row(row)
            listing, errors = self._listing_from_row(normalized_row, unknown, payload, row_number)
            if errors:
                result.rows_skipped += 1
                result.errors.extend(errors)
                continue
            result.rows_imported += 1
            result.listings.append(listing)

        if not result.listings:
            result.warnings.append("No listings were imported from the CSV payload.")
        return result

    @staticmethod
    def _normalize_row(row: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        normalized: dict[str, Any] = {}
        unknown: dict[str, Any] = {}
        for key, value in row.items():
            if key is None:
                unknown["__extra_values"] = value
                continue
            canonical = canonical_column(key)
            if canonical:
                normalized[canonical] = value
            else:
                unknown[key] = value
        return normalized, unknown

    def _listing_from_row(
        self,
        row: dict[str, Any],
        unknown: dict[str, Any],
        payload: CsvImportRequest,
        row_number: int,
    ) -> tuple[NormalizedListing | None, list[dict[str, Any]]]:
        errors = []
        price = parse_money(row.get("price_monthly"))
        bedrooms = parse_int(row.get("bedrooms"))
        bathrooms = parse_float(row.get("bathrooms"))
        city = clean_text(row.get("city"))
        title = clean_text(row.get("title")) or f"{city or 'Unknown'} CSV listing"

        for field_name, value in {"price_monthly": price, "bedrooms": bedrooms, "bathrooms": bathrooms, "city": city}.items():
            if value is None:
                errors.append({"row_number": row_number, "message": f"Missing or invalid {field_name}."})

        if errors:
            return None, errors

        backyard_status = normalize_status(row.get("backyard_status"))
        garage_status = normalize_status(row.get("garage_status"))
        pets_allowed = bool_from_text(row.get("pet_policy"))
        pet_policy = clean_text(row.get("pet_policy"))
        if pets_allowed is not None and pet_policy is None:
            pet_policy = "Pets allowed" if pets_allowed else "Pets not allowed"

        listing = NormalizedListing(
            title=title,
            description=clean_text(row.get("description")),
            address=clean_text(row.get("address")),
            city=city,
            county=clean_text(row.get("county")) or "Orange County",
            state=clean_text(row.get("state")) or "CA",
            zip=clean_text(row.get("zip")),
            neighborhood=clean_text(row.get("neighborhood")),
            price_monthly=price,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            square_feet=parse_int(row.get("square_feet")),
            lot_size=parse_int(row.get("lot_size")),
            property_type=clean_text(row.get("property_type")) or "unknown",
            backyard_status=backyard_status,
            garage_status=garage_status,
            parking_details=clean_text(row.get("parking_details")),
            pet_policy=pet_policy,
            notes=clean_text(row.get("notes")) or payload.notes,
            feature_tags=[
                tag
                for tag, status in {"backyard": backyard_status, "garage": garage_status}.items()
                if status == "yes"
            ]
            + ["csv"],
            provenance=Provenance(
                source_name=payload.source_name or self.source_name,
                source_type=self.source_type,
                source_url=clean_text(row.get("source_url")),
                source_listing_id=clean_text(row.get("source_listing_id")),
                source_confidence=confidence_for_source(self.source_type),
                raw_payload_json={"row": row, "unknown_columns": unknown},
            ),
        )
        return listing, []
