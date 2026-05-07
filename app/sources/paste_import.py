from __future__ import annotations

import re

from app.schemas import PasteImportRequest
from app.sources.base import IngestionResult, NormalizedListing, Provenance, confidence_for_source
from app.sources.normalizer import clean_text, find_evidence, infer_feature_status, infer_oc_city, parse_float, parse_int, parse_money
from app.sources.source_inference import infer_source_from_url, normalize_domain


class PasteImportAdapter:
    source_name = "Paste Import"
    source_type = "paste"
    enabled_by_default = True

    def ingest(self, payload: PasteImportRequest) -> IngestionResult:
        text = payload.raw_text
        source_url = str(payload.source_url) if payload.source_url else None
        source_name = payload.source_name or infer_source_from_url(source_url) or self.source_name

        price = self._extract_price(text)
        bedrooms = self._extract_bedrooms(text)
        bathrooms = self._extract_bathrooms(text)
        sqft = self._extract_square_feet(text)
        address = self._extract_address(text)
        state, zip_code = self._extract_state_zip(text)
        city = infer_oc_city(text) or "Unknown"
        backyard_status, backyard_evidence = infer_feature_status(
            text,
            [
                "backyard",
                "back yard",
                "private yard",
                "fenced yard",
                "yard",
                "patio",
                "outdoor space",
                "garden",
                "lawn",
                "deck",
                "courtyard",
            ],
            ["no yard", "no backyard", "no private yard", "shared courtyard only"],
        )
        garage_status, garage_evidence = infer_feature_status(
            text,
            [
                "garage",
                "attached garage",
                "detached garage",
                "2 car garage",
                "two car garage",
                "two-car garage",
                "parking garage",
                "covered parking",
                "carport",
            ],
            ["no garage", "street parking only"],
        )
        parking_details = find_evidence(text, ["parking", "garage", "driveway", "carport"])
        pet_policy = find_evidence(text, ["pet", "dog", "cat"])
        laundry = find_evidence(text, ["laundry", "washer", "dryer"])
        air_conditioning = find_evidence(text, ["air conditioning", "a/c", "central air", "central ac"])

        errors = []
        if price is None:
            errors.append({"row_number": None, "message": "Could not find a monthly price."})
        if bedrooms is None:
            errors.append({"row_number": None, "message": "Could not find bedroom count."})
        if bathrooms is None:
            errors.append({"row_number": None, "message": "Could not find bathroom count."})

        if errors:
            return IngestionResult(rows_received=1, rows_skipped=1, errors=errors)

        completeness = sum(
            value is not None and value != "unknown"
            for value in [price, bedrooms, bathrooms, sqft, city, backyard_status, garage_status]
        ) / 7
        title = self._extract_title(text) or f"{city} pasted listing"
        listing = NormalizedListing(
            title=title,
            city=city,
            price_monthly=price,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            square_feet=sqft,
            address=address,
            state=state or "CA",
            zip=zip_code,
            backyard_status=backyard_status,
            backyard_evidence=backyard_evidence,
            garage_status=garage_status,
            garage_evidence=garage_evidence,
            parking_details=parking_details,
            pet_policy=pet_policy,
            laundry=laundry,
            air_conditioning=air_conditioning,
            description=clean_text(text[:500]),
            notes=payload.notes,
            feature_tags=[tag for tag, status in {"backyard": backyard_status, "garage": garage_status}.items() if status == "yes"] + ["paste"],
            provenance=Provenance(
                source_name=source_name,
                source_type=self.source_type,
                source_url=source_url,
                source_domain=normalize_domain(source_url),
                source_confidence=confidence_for_source(self.source_type, completeness),
                raw_text=text,
                raw_payload_json={"parser": "deterministic_regex_v1"},
            ),
        )
        return IngestionResult(listings=[listing], rows_received=1, rows_imported=1)

    @staticmethod
    def _extract_price(text: str) -> float | None:
        rent_match = re.search(r"\$[\s]*[0-9][0-9,]*(?:\.\d{1,2})?\s*(?:/mo|per month|monthly|month)?", text, re.I)
        return parse_money(rent_match.group(0)) if rent_match else None

    @staticmethod
    def _extract_bedrooms(text: str) -> int | None:
        match = re.search(r"(\d+)\s*(?:bed|beds|bedroom|bedrooms|bd|br)\b", text, re.I)
        return parse_int(match.group(1)) if match else None

    @staticmethod
    def _extract_bathrooms(text: str) -> float | None:
        match = re.search(r"(\d+(?:\.\d+)?)\s*(?:bath|baths|bathroom|bathrooms|ba)\b", text, re.I)
        return parse_float(match.group(1)) if match else None

    @staticmethod
    def _extract_square_feet(text: str) -> int | None:
        match = re.search(r"([0-9][0-9,]*)\s*(?:sq\.?\s*ft|sqft|square feet|sf)\b", text, re.I)
        return parse_int(match.group(1)) if match else None

    @staticmethod
    def _extract_address(text: str) -> str | None:
        street_types = (
            "Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Court|Ct|Way|"
            "Circle|Cir|Boulevard|Blvd|Place|Pl|Trail|Trl|Parkway|Pkwy|Terrace|Ter|Loop|Cove"
        )
        pattern = re.compile(
            rf"\b\d{{1,6}}\s+[A-Za-z0-9][A-Za-z0-9 .'-]*\s(?:{street_types})\.?"
            r"(?:\s*(?:Unit|Apt|Apartment|#)\s*[A-Za-z0-9-]+)?",
            re.I,
        )
        match = pattern.search(text)
        return clean_text(match.group(0)) if match else None

    @staticmethod
    def _extract_state_zip(text: str) -> tuple[str | None, str | None]:
        match = re.search(r"\b(CA|California)\s+(\d{5}(?:-\d{4})?)\b", text, re.I)
        if not match:
            return None, None
        return "CA", match.group(2)

    @staticmethod
    def _extract_title(text: str) -> str | None:
        for line in text.splitlines():
            cleaned = clean_text(line)
            if cleaned and not cleaned.startswith("$") and len(cleaned) > 8:
                return cleaned[:180]
        return None
