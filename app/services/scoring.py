from __future__ import annotations

from datetime import datetime
from typing import Iterable

from app.config import DEFAULT_SCORE_WEIGHTS
from app.models import Listing, SearchCriteria
from app.services.benchmark_service import Benchmark, get_benchmark_for_city


def clamp(value: float, floor: float = 0.0, ceiling: float = 100.0) -> float:
    return max(floor, min(ceiling, value))


def _price_per_bedroom(listing: Listing) -> float | None:
    if listing.bedrooms <= 0 or float(listing.price) <= 0:
        return None
    return round(float(listing.price) / listing.bedrooms, 2)


def _price_per_sqft(listing: Listing) -> float | None:
    if not listing.square_feet or listing.square_feet <= 0 or float(listing.price) <= 0:
        return None
    return round(float(listing.price) / listing.square_feet, 2)


def _price_score(listing: Listing, criteria: SearchCriteria) -> float:
    if float(listing.price) <= 0:
        return 0.0
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
    if not criteria.require_backyard:
        score += 20.0
    elif listing.backyard_status == "yes":
        score += 20.0
    elif listing.backyard_status == "unknown":
        score += 10.0
    if not criteria.require_garage:
        score += 20.0
    elif listing.garage_status == "yes":
        score += 20.0
    elif listing.garage_status == "unknown":
        score += 10.0
    if listing.pets_allowed:
        score += 10.0
    if listing.garage_spaces and listing.garage_spaces >= 2:
        score += 10.0
    return clamp(score)


def _freshness_score(listing: Listing) -> float:
    timestamp = listing.updated_at or listing.last_seen_at or listing.imported_at or listing.listed_at or listing.first_seen_at
    if not timestamp:
        return 50.0
    days_old = max((datetime.utcnow() - timestamp).days, 0)
    return clamp(100 - days_old * 4.5)


def _confidence_score(listing: Listing) -> float:
    score = clamp((listing.source_confidence or listing.confidence) * 100)
    if listing.backyard_status == "yes" and listing.backyard_evidence:
        score += 5
    if listing.garage_status == "yes" and listing.garage_evidence:
        score += 5
    if listing.raw_text:
        score += 4
    if listing.source_url or listing.listing_url:
        score += 4
    if listing.source_type == "url_reference":
        score -= 20
    if listing.backyard_status == "unknown":
        score -= 8
    if listing.garage_status == "unknown":
        score -= 8
    if not listing.square_feet:
        score -= 6
    return clamp(score)


def _hard_criteria_score(listing: Listing, criteria: SearchCriteria) -> float:
    score = 0.0
    score += 25.0 if listing.county.lower() == criteria.county.lower() and listing.state == criteria.state else 0.0
    score += 25.0 if listing.bedrooms >= criteria.min_bedrooms else clamp((listing.bedrooms / max(criteria.min_bedrooms, 1)) * 25)

    if not criteria.require_backyard:
        score += 25.0
    elif listing.backyard_status == "yes":
        score += 25.0
    elif listing.backyard_status == "unknown":
        score += 12.5

    if not criteria.require_garage:
        score += 25.0
    elif listing.garage_status == "yes":
        score += 25.0
    elif listing.garage_status == "unknown":
        score += 12.5
    return clamp(score)


def _data_completeness_score(listing: Listing) -> float:
    fields = [
        listing.title,
        listing.city,
        listing.county,
        listing.state,
        float(listing.price) > 0,
        listing.bedrooms > 0,
        listing.bathrooms > 0,
        listing.square_feet,
        listing.backyard_status != "unknown",
        listing.garage_status != "unknown",
        listing.parking_details,
        listing.pet_policy,
        listing.source_url or listing.listing_url,
    ]
    return round(sum(bool(field) for field in fields) / len(fields) * 100, 2)


def _source_reliability_score(listing: Listing) -> float:
    source_type = listing.source_type or (listing.source.kind if listing.source else "unknown")
    base = {
        "manual": 88,
        "paste": 66,
        "file": 76,
        "csv": 76,
        "browser_clip": 72,
        "url_reference": 40,
        "provider_feed": 84,
        "provider_api": 88,
        "approved_provider": 86,
        "web": 48,
        "licensed_api": 90,
    }.get(source_type, 58)
    if listing.source and listing.source.status == "disabled":
        base -= 15
    return clamp(float(base))


def _market_label(price: float, benchmark: Benchmark) -> str:
    if price < benchmark.typical_low_3br:
        return "below_typical_low"
    if price < benchmark.median_rent_3br:
        return "below_market"
    if price <= benchmark.typical_high_3br:
        return "near_market"
    return "above_typical_high"


def _range_value_component(value: float, low: float, median: float, high: float) -> float:
    if value <= 0:
        return 0.0
    lower_width = max(median - low, median * 0.08)
    upper_width = max(high - median, median * 0.08)
    if value < low:
        return clamp(92 + ((low - value) / lower_width) * 8)
    if value < median:
        return clamp(68 + ((median - value) / lower_width) * 22)
    if value <= high:
        return clamp(68 - ((value - median) / upper_width) * 36)
    return clamp(32 - ((value - high) / upper_width) * 27)


def _benchmark_context(listing: Listing, benchmark: Benchmark | None) -> dict:
    price = float(listing.price)
    ppsf = _price_per_sqft(listing)
    if benchmark is None or price <= 0:
        return {
            "benchmark_used": False,
            "benchmark_city": None,
            "benchmark_used_fallback": False,
            "benchmark_confidence": None,
            "median_rent_3br": None,
            "typical_low_3br": None,
            "typical_high_3br": None,
            "rent_delta_vs_median": None,
            "rent_delta_percent": None,
            "price_per_sqft_delta": None,
            "market_label": "unknown",
            "benchmark_notes": None,
            "benchmark_sources": [],
        }

    rent_delta = round(price - benchmark.median_rent_3br, 2)
    rent_delta_percent = round((price - benchmark.median_rent_3br) / benchmark.median_rent_3br * 100, 2)
    context = benchmark.to_context()
    context.update(
        {
            "rent_delta_vs_median": rent_delta,
            "rent_delta_percent": rent_delta_percent,
            "price_per_sqft_delta": round(ppsf - benchmark.median_price_per_sqft, 2) if ppsf else None,
            "market_label": _market_label(price, benchmark),
        }
    )
    return context


def _deal_score(listing: Listing, criteria: SearchCriteria) -> tuple[float, list[str], list[str], dict]:
    reasons: list[str] = []
    warnings: list[str] = []
    benchmark = get_benchmark_for_city(listing.city)
    benchmark_context = _benchmark_context(listing, benchmark)
    price = float(listing.price)
    space_score = _space_score(listing, criteria)
    freshness_score = _freshness_score(listing)
    completeness_score = _data_completeness_score(listing)
    confidence_score = _confidence_score(listing)

    if price <= 0:
        return 0.0, reasons, ["Monthly rent is missing, so deal score is low."], benchmark_context

    if benchmark:
        rent_component = _range_value_component(price, benchmark.typical_low_3br, benchmark.median_rent_3br, benchmark.typical_high_3br)
        ppsf = _price_per_sqft(listing)
        if ppsf:
            ppsf_component = _range_value_component(
                ppsf,
                benchmark.typical_low_price_per_sqft,
                benchmark.median_price_per_sqft,
                benchmark.typical_high_price_per_sqft,
            )
        else:
            ppsf_component = 50
            warnings.append("Square footage is missing, so price-per-square-foot comparison is limited.")

        price_per_bedroom = _price_per_bedroom(listing)
        if price_per_bedroom:
            expected_price_per_bedroom = benchmark.median_rent_3br / 3
            ppb_component = clamp((1.18 - (price_per_bedroom / expected_price_per_bedroom)) / 0.45 * 100)
        else:
            ppb_component = 45
            warnings.append("Bedroom count is missing, so price-per-bedroom comparison is limited.")

        delta_amount = abs(benchmark_context["rent_delta_vs_median"])
        delta_percent = abs(benchmark_context["rent_delta_percent"])
        city_label = benchmark.city
        if benchmark.used_fallback:
            warnings.append(f"No city benchmark found for {listing.city or 'this city'}; using Orange County fallback.")
        if benchmark.benchmark_confidence in {"low", "fallback", "unknown"}:
            warnings.append("Benchmark confidence is low; verify market comparison manually.")

        if price < benchmark.typical_low_3br:
            reasons.append(f"Rent is ${delta_amount:,.0f} below the {city_label} 3BR benchmark.")
            warnings.append("Rent is below the typical low range; verify listing quality, fees, and scam risk.")
        elif price < benchmark.median_rent_3br:
            reasons.append(f"Rent is {delta_percent:.0f}% below the {city_label} 3BR benchmark.")
        elif price <= benchmark.typical_high_3br:
            reasons.append(f"Rent is near the {city_label} 3BR benchmark range.")
        else:
            warnings.append(f"Rent is ${delta_amount:,.0f} above the {city_label} 3BR benchmark.")

        if ppsf and ppsf > benchmark.typical_high_price_per_sqft:
            warnings.append("Price per sqft is above the city typical range.")
        elif ppsf and ppsf < benchmark.typical_low_price_per_sqft:
            reasons.append("Price per sqft is below the city typical range.")
    else:
        rent_component = _price_score(listing, criteria)
        ppsf_component = 50 if not listing.square_feet else clamp(100 - (_price_per_sqft(listing) or 0) * 20)
        ppb_component = 50
        warnings.append("No city benchmark exists for this city; deal score uses fallback heuristics.")

    feature_modifier = 0
    if listing.backyard_status == "yes":
        feature_modifier += 5
    elif listing.backyard_status == "unknown":
        feature_modifier -= 3
    else:
        feature_modifier -= 15
    if listing.garage_status == "yes":
        feature_modifier += 5
    elif listing.garage_status == "unknown":
        feature_modifier -= 3
    else:
        feature_modifier -= 15

    deal = (
        rent_component * 0.42
        + ppsf_component * 0.17
        + ppb_component * 0.13
        + space_score * 0.10
        + freshness_score * 0.06
        + confidence_score * 0.06
        + completeness_score * 0.06
        + feature_modifier
    )
    if benchmark:
        deal *= benchmark.confidence_multiplier
    return round(clamp(deal), 2), reasons, warnings, benchmark_context


def _needs_review(listing: Listing, deal_score: float, match_score: float) -> tuple[list[str], list[str]]:
    badges: list[str] = []
    next_actions: list[str] = []
    promising = listing.bedrooms >= 3 and float(listing.price) > 0 and deal_score >= 55
    if promising and listing.backyard_status == "unknown":
        badges.append("Verify backyard")
        next_actions.append("Verify backyard availability")
    if promising and listing.garage_status == "unknown":
        badges.append("Verify garage")
        next_actions.append("Verify garage availability")
    if (listing.source_url or listing.listing_url) and _data_completeness_score(listing) < 80:
        badges.append("Check source")
        next_actions.append("Check listing source URL")
    if not listing.square_feet:
        badges.append("Missing sqft")
        next_actions.append("Find square footage")
    if deal_score >= 70 and match_score >= 65:
        badges.append("Possibly good deal")
    if listing.city and listing.county.lower() == "orange county" and not listing.address_line1:
        badges.append("Missing address")
        next_actions.append("Verify address or cross streets")
    return badges, list(dict.fromkeys(next_actions))


def _score_reasons_and_warnings(listing: Listing, criteria: SearchCriteria, deal_score: float) -> tuple[list[str], list[str], list[str], list[str]]:
    reasons: list[str] = []
    warnings: list[str] = []

    if listing.county.lower() == criteria.county.lower() and listing.state == criteria.state:
        reasons.append("Located in Orange County CA.")
    else:
        warnings.append("Listing is outside the Orange County CA hard criteria.")
    if listing.bedrooms >= criteria.min_bedrooms:
        reasons.append("Meets 3+ bedroom requirement.")
    else:
        warnings.append("Under the 3 bedroom minimum.")
    if listing.backyard_status == "yes":
        reasons.append("Backyard is confirmed.")
    elif listing.backyard_status == "unknown":
        warnings.append("Backyard is unknown and needs manual verification.")
    else:
        warnings.append("Backyard is confirmed unavailable.")
    if listing.garage_status == "yes":
        reasons.append("Garage is confirmed.")
    elif listing.garage_status == "unknown":
        warnings.append("Garage is unknown and needs manual verification.")
    else:
        warnings.append("Garage is confirmed unavailable.")
    if listing.square_feet:
        reasons.append(f"Price per square foot is ${_price_per_sqft(listing):.2f}.")
    else:
        warnings.append("Square footage is missing, reducing deal and completeness confidence.")
    if listing.source_url or listing.listing_url:
        reasons.append("Source URL is stored for provenance.")
    else:
        warnings.append("Source URL is missing.")

    badges, next_actions = _needs_review(listing, deal_score, _hard_criteria_score(listing, criteria))
    if listing.decision_status in {"new", "needs_review"} and badges:
        next_actions = next_actions or ["Review missing listing details"]
    if not next_actions and listing.decision_status in {"new", "promising"}:
        next_actions.append("Contact property manager")
    return reasons, warnings, next_actions, badges


def compute_listing_score(listing: Listing, criteria: SearchCriteria) -> dict:
    weights = DEFAULT_SCORE_WEIGHTS | (criteria.weights or {})
    hard_criteria_score = _hard_criteria_score(listing, criteria)
    price_score = _price_score(listing, criteria)
    space_score = _space_score(listing, criteria)
    location_score = _location_score(listing, criteria)
    feature_score = _feature_score(listing, criteria)
    freshness_score = _freshness_score(listing)
    confidence_score = _confidence_score(listing)
    data_completeness_score = _data_completeness_score(listing)
    source_reliability_score = _source_reliability_score(listing)
    deal_score, deal_reasons, deal_warnings, benchmark_context = _deal_score(listing, criteria)

    total = (
        hard_criteria_score * 0.28
        + deal_score * 0.24
        + confidence_score * 0.14
        + data_completeness_score * 0.14
        + freshness_score * 0.10
        + source_reliability_score * 0.10
    )
    reasons, warnings, next_actions, needs_review_badges = _score_reasons_and_warnings(listing, criteria, deal_score)
    reasons.extend(deal_reasons)
    warnings.extend(deal_warnings)
    reasons = list(dict.fromkeys(reasons))
    warnings = list(dict.fromkeys(warnings))

    return {
        "total_score": round(total, 2),
        "price_score": round(price_score, 2),
        "space_score": round(space_score, 2),
        "location_score": round(location_score, 2),
        "feature_score": round(feature_score, 2),
        "freshness_score": round(freshness_score, 2),
        "confidence_score": round(confidence_score, 2),
        "hard_criteria_score": round(hard_criteria_score, 2),
        "match_score": round(hard_criteria_score, 2),
        "deal_score": round(deal_score, 2),
        "data_completeness_score": round(data_completeness_score, 2),
        "completeness_score": round(data_completeness_score, 2),
        "source_reliability_score": round(source_reliability_score, 2),
        "overall_score": round(total, 2),
        "price_per_bedroom": _price_per_bedroom(listing),
        "price_per_sqft": _price_per_sqft(listing),
        **benchmark_context,
        "reasons": reasons,
        "warnings": warnings,
        "next_actions": next_actions,
        "needs_review_badges": needs_review_badges,
        "explanation": {
            "headline": (
                f"{listing.title} balances ${float(listing.price):,.0f}/mo pricing "
                f"with {listing.bedrooms} bd / {listing.bathrooms:g} ba and "
                f"{listing.square_feet or 'unknown'} sqft."
            ),
            "reasons": reasons,
            "warnings": warnings,
            "next_actions": next_actions,
            "needs_review_badges": needs_review_badges,
            "price_per_bedroom": _price_per_bedroom(listing),
            "price_per_sqft": _price_per_sqft(listing),
            "overall_score": round(total, 2),
            "match_score": round(hard_criteria_score, 2),
            "completeness_score": round(data_completeness_score, 2),
            "weights": weights,
            "benchmark_context": benchmark_context,
            "score_model": {
                "hard_criteria": "Orange County CA, minimum bedrooms, backyard status, garage status",
                "deal": "Editable city/county 3BR benchmark, typical low/high range, price per bedroom, price per square foot, space, freshness, confidence, and completeness",
                "unknown_features": "Unknown backyard/garage receives partial credit below confirmed yes and above confirmed no.",
                "freshness": "Uses updated/imported/seen timestamps when source listing freshness is unavailable.",
            },
        },
    }


def rank_listings(
    listings: Iterable[Listing],
    criteria: SearchCriteria,
) -> list[tuple[Listing, dict]]:
    ranked = [(listing, compute_listing_score(listing, criteria)) for listing in listings]
    ranked.sort(key=lambda item: item[1]["total_score"], reverse=True)
    return ranked
