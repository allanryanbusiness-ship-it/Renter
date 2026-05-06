from __future__ import annotations

from datetime import datetime
from typing import Iterable

from app.config import DEFAULT_SCORE_WEIGHTS
from app.models import Listing, SearchCriteria


def clamp(value: float, floor: float = 0.0, ceiling: float = 100.0) -> float:
    return max(floor, min(ceiling, value))


def _price_score(listing: Listing, criteria: SearchCriteria) -> float:
    if criteria.max_price:
        return clamp((criteria.max_price / float(listing.price)) * 100)
    return clamp(100 - float(listing.price) / 120)


def _space_score(listing: Listing, criteria: SearchCriteria) -> float:
    bedroom_component = clamp((listing.bedrooms / max(criteria.min_bedrooms, 1)) * 45)
    bathroom_component = clamp((listing.bathrooms / max(criteria.min_bathrooms, 1)) * 20)
    sqft_target = criteria.min_sqft or 1400
    sqft_component = clamp(((listing.square_feet or sqft_target) / sqft_target) * 35)
    return clamp(bedroom_component + bathroom_component + sqft_component)


def _location_score(listing: Listing, criteria: SearchCriteria) -> float:
    score = 35.0
    if listing.county.lower() == criteria.county.lower():
        score += 35.0
    if criteria.city and listing.city.lower() == criteria.city.lower():
        score += 20.0
    if listing.neighborhood:
        score += 10.0
    return clamp(score)


def _feature_score(listing: Listing, criteria: SearchCriteria) -> float:
    score = 20.0
    if listing.bedrooms >= criteria.min_bedrooms:
        score += 20.0
    if not criteria.require_backyard or listing.has_backyard:
        score += 20.0
    if not criteria.require_garage or listing.has_garage:
        score += 20.0
    if listing.pets_allowed:
        score += 10.0
    if listing.garage_spaces and listing.garage_spaces >= 2:
        score += 10.0
    return clamp(score)


def _freshness_score(listing: Listing) -> float:
    if not listing.listed_at:
        return 50.0
    days_old = max((datetime.utcnow() - listing.listed_at).days, 0)
    return clamp(100 - days_old * 4.5)


def _confidence_score(listing: Listing) -> float:
    return clamp(listing.confidence * 100)


def compute_listing_score(listing: Listing, criteria: SearchCriteria) -> dict:
    weights = DEFAULT_SCORE_WEIGHTS | (criteria.weights or {})
    price_score = _price_score(listing, criteria)
    space_score = _space_score(listing, criteria)
    location_score = _location_score(listing, criteria)
    feature_score = _feature_score(listing, criteria)
    freshness_score = _freshness_score(listing)
    confidence_score = _confidence_score(listing)

    total = (
        price_score * weights["price"]
        + space_score * weights["space"]
        + location_score * weights["location"]
        + feature_score * weights["features"]
        + freshness_score * weights["freshness"]
        + confidence_score * weights["confidence"]
    )

    return {
        "total_score": round(total, 2),
        "price_score": round(price_score, 2),
        "space_score": round(space_score, 2),
        "location_score": round(location_score, 2),
        "feature_score": round(feature_score, 2),
        "freshness_score": round(freshness_score, 2),
        "confidence_score": round(confidence_score, 2),
        "explanation": {
            "headline": (
                f"{listing.title} balances ${float(listing.price):,.0f}/mo pricing "
                f"with {listing.bedrooms} bd / {listing.bathrooms:g} ba and "
                f"{listing.square_feet or 'unknown'} sqft."
            ),
            "weights": weights,
        },
    }


def rank_listings(
    listings: Iterable[Listing],
    criteria: SearchCriteria,
) -> list[tuple[Listing, dict]]:
    ranked = [(listing, compute_listing_score(listing, criteria)) for listing in listings]
    ranked.sort(key=lambda item: item[1]["total_score"], reverse=True)
    return ranked

