from datetime import datetime
from decimal import Decimal

from app.models import Listing, SearchCriteria, Source
from app.services.scoring import compute_listing_score


def _listing(backyard_status: str, garage_status: str) -> Listing:
    listing = Listing(
        source=Source(name="Paste Import", kind="paste", adapter_key="paste_import", status="active"),
        title="Irvine Test Listing",
        city="Irvine",
        county="Orange County",
        state="CA",
        price=Decimal("4500"),
        bedrooms=3,
        bathrooms=2.5,
        square_feet=1800,
        backyard_status=backyard_status,
        garage_status=garage_status,
        has_backyard=backyard_status == "yes",
        has_garage=garage_status == "yes",
        confidence=0.7,
        source_confidence=0.7,
        listed_at=datetime.utcnow(),
        feature_tags=[],
        raw_payload={},
    )
    return listing


def _criteria() -> SearchCriteria:
    return SearchCriteria(
        name="OC",
        county="Orange County",
        state="CA",
        min_bedrooms=3,
        min_bathrooms=2,
        max_price=6500,
        min_sqft=1400,
        require_backyard=True,
        require_garage=True,
        weights={},
    )


def test_unknown_backyard_and_garage_rank_between_yes_and_no() -> None:
    criteria = _criteria()
    yes_score = compute_listing_score(_listing("yes", "yes"), criteria)["hard_criteria_score"]
    unknown_score = compute_listing_score(_listing("unknown", "unknown"), criteria)["hard_criteria_score"]
    no_score = compute_listing_score(_listing("no", "no"), criteria)["hard_criteria_score"]

    assert yes_score > unknown_score > no_score


def test_score_breakdown_includes_deal_metrics_and_explanations() -> None:
    score = compute_listing_score(_listing("yes", "yes"), _criteria())

    assert score["match_score"] == score["hard_criteria_score"]
    assert score["deal_score"] > 0
    assert score["price_per_bedroom"] == 1500
    assert score["price_per_sqft"] == 2.5
    assert score["reasons"]
    assert score["benchmark_used"] is True
    assert score["benchmark_city"] == "Irvine"
    assert score["median_rent_3br"] == 4386
    assert score["rent_delta_vs_median"] == 114
    assert score["market_label"] == "near_market"


def test_confirmed_no_feature_penalty_is_strong() -> None:
    criteria = _criteria()
    yes = compute_listing_score(_listing("yes", "yes"), criteria)
    no = compute_listing_score(_listing("no", "no"), criteria)

    assert yes["match_score"] - no["match_score"] >= 40
    assert yes["total_score"] > no["total_score"]


def test_confidence_score_rewards_evidence_and_source_url() -> None:
    listing = _listing("yes", "yes")
    listing.backyard_evidence = "Private fenced backyard."
    listing.garage_evidence = "Attached garage."
    listing.source_url = "https://example.com/listing"
    listing.raw_text = "Private fenced backyard. Attached garage."

    score = compute_listing_score(listing, _criteria())

    assert score["confidence_score"] > 70
