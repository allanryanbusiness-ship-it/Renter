from decimal import Decimal

from tests.test_scoring import _criteria, _listing

from app.services.scoring import compute_listing_score


def test_below_median_listing_gets_positive_benchmark_reason() -> None:
    listing = _listing("yes", "yes")
    listing.city = "Irvine"
    listing.price = Decimal("3900")

    score = compute_listing_score(listing, _criteria())

    assert score["benchmark_used"] is True
    assert score["benchmark_city"] == "Irvine"
    assert score["rent_delta_vs_median"] < 0
    assert score["market_label"] in {"below_market", "below_typical_low"}
    assert any("below" in reason.lower() and "irvine" in reason.lower() for reason in score["reasons"])


def test_above_typical_high_listing_gets_penalized_and_warned() -> None:
    listing = _listing("yes", "yes")
    listing.city = "Irvine"
    listing.price = Decimal("6200")

    score = compute_listing_score(listing, _criteria())

    assert score["rent_delta_vs_median"] > 0
    assert score["market_label"] == "above_typical_high"
    assert score["deal_score"] < 55
    assert any("above" in warning.lower() and "irvine" in warning.lower() for warning in score["warnings"])


def test_low_confidence_benchmark_adds_warning() -> None:
    listing = _listing("yes", "yes")
    listing.city = "Lake Forest"
    listing.price = Decimal("3900")

    score = compute_listing_score(listing, _criteria())

    assert score["benchmark_confidence"] == "low"
    assert any("benchmark confidence is low" in warning.lower() for warning in score["warnings"])


def test_missing_city_benchmark_uses_county_fallback_in_score_breakdown() -> None:
    listing = _listing("yes", "yes")
    listing.city = "Laguna Beach"
    listing.price = Decimal("4300")

    score = compute_listing_score(listing, _criteria())

    assert score["benchmark_used"] is True
    assert score["benchmark_used_fallback"] is True
    assert score["benchmark_city"] == "Orange County"
    assert any("county fallback" in warning.lower() for warning in score["warnings"])
