from __future__ import annotations

from typing import Any

from app.schemas import ManualListingCreate


def clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = " ".join(value.split())
    return stripped or None


def normalize_manual_listing(payload: ManualListingCreate) -> dict[str, Any]:
    feature_tags = []
    if payload.has_backyard:
        feature_tags.append("backyard")
    if payload.has_garage:
        feature_tags.append("garage")
    if payload.pets_allowed:
        feature_tags.append("pets")
    if payload.square_feet and payload.square_feet >= 2000:
        feature_tags.append("spacious")

    return {
        "title": clean_text(payload.title) or "Untitled Listing",
        "address_line1": clean_text(payload.address_line1),
        "city": clean_text(payload.city) or "Unknown",
        "neighborhood": clean_text(payload.neighborhood),
        "county": clean_text(payload.county) or "Orange County",
        "state": clean_text(payload.state) or "CA",
        "postal_code": clean_text(payload.postal_code),
        "price": float(payload.price),
        "bedrooms": int(payload.bedrooms),
        "bathrooms": float(payload.bathrooms),
        "square_feet": payload.square_feet,
        "lot_size_sqft": payload.lot_size_sqft,
        "has_backyard": bool(payload.has_backyard),
        "has_garage": bool(payload.has_garage),
        "garage_spaces": payload.garage_spaces,
        "pets_allowed": payload.pets_allowed,
        "watchlist_status": clean_text(payload.watchlist_status) or "review",
        "property_type": clean_text(payload.property_type) or "single_family",
        "listing_url": str(payload.listing_url) if payload.listing_url else None,
        "image_url": str(payload.image_url) if payload.image_url else None,
        "description": clean_text(payload.description),
        "feature_tags": feature_tags,
        "confidence": 0.95,
        "raw_payload": payload.model_dump(mode="json"),
    }

