from __future__ import annotations

import re
import logging
from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session, selectinload

from app.config import DEFAULT_SEARCH_CRITERIA
from app.models import ImportRun, Listing, ListingNote, ListingScore, SearchCriteria, Source, WatchlistEntry
from app.schemas import (
    BrowserClipImportData,
    BrowserClipImportResponse,
    BrowserClipRequest,
    CsvImportRequest,
    CsvImportSummary,
    ImportErrorRead,
    ListingDecisionUpdate,
    ListingFilterParams,
    ListingRead,
    ListingNotesUpdate,
    ListingWatchlistUpdate,
    ManualListingCreate,
    PasteImportRequest,
    ScoreBreakdownRead,
    SearchCriteriaUpdate,
    UrlReferenceCreate,
)
from app.sources import CsvImportAdapter, ManualEntryAdapter, PasteImportAdapter, UrlReferenceAdapter
from app.sources.base import IngestionResult, NormalizedListing
from app.sources.browser_clip import BrowserClipAdapter, extracted_fields_for
from app.services.scoring import compute_listing_score


logger = logging.getLogger(__name__)
MAX_BROWSER_CLIP_TOTAL_CHARS = 50_000

SOURCE_CATALOG = [
    {
        "name": "Manual Import",
        "kind": "manual",
        "adapter_key": "manual",
        "status": "active",
        "base_url": None,
        "enabled_by_default": True,
        "compliance_notes": "User-provided URLs and pasted details.",
    },
    {
        "name": "CSV Import",
        "kind": "file",
        "adapter_key": "csv_import",
        "status": "active",
        "base_url": None,
        "enabled_by_default": True,
        "compliance_notes": "User-controlled CSV text or file contents.",
    },
    {
        "name": "Paste Import",
        "kind": "paste",
        "adapter_key": "paste_import",
        "status": "active",
        "base_url": None,
        "enabled_by_default": True,
        "compliance_notes": "User-pasted listing text parsed with deterministic local regexes.",
    },
    {
        "name": "URL Reference",
        "kind": "url_reference",
        "adapter_key": "url_reference",
        "status": "active",
        "base_url": None,
        "enabled_by_default": True,
        "compliance_notes": "Reference-only URL capture; no page scraping.",
    },
    {
        "name": "Browser Clip",
        "kind": "browser_clip",
        "adapter_key": "browser_clip",
        "status": "active",
        "base_url": None,
        "enabled_by_default": True,
        "compliance_notes": "User-triggered bookmarklet or fallback JSON import; no server-side page fetch.",
    },
    {
        "name": "Approved Demo Provider Feed",
        "kind": "provider_feed",
        "adapter_key": "approved_demo_feed",
        "status": "active",
        "base_url": None,
        "enabled_by_default": True,
        "compliance_notes": "Local provider-style automatic discovery feed; no external page fetches.",
    },
    {
        "name": "Mock Discovery Provider",
        "kind": "mock_provider",
        "adapter_key": "mock",
        "status": "active",
        "base_url": None,
        "enabled_by_default": False,
        "compliance_notes": "Local mock automatic discovery provider; no external calls.",
    },
    {
        "name": "RentCast",
        "kind": "provider_api",
        "adapter_key": "rentcast",
        "status": "available",
        "base_url": "https://api.rentcast.io/v1/listings/rental/long-term",
        "enabled_by_default": False,
        "compliance_notes": "Provider API adapter; requires user's API key and explicit enablement.",
    },
    {
        "name": "Apify Placeholder",
        "kind": "provider_placeholder",
        "adapter_key": "apify",
        "status": "disabled",
        "base_url": "https://apify.com/",
        "enabled_by_default": False,
        "compliance_notes": "Disabled placeholder pending compliance review and provider-specific tests.",
    },
    {
        "name": "Bright Data Placeholder",
        "kind": "provider_placeholder",
        "adapter_key": "brightdata",
        "status": "disabled",
        "base_url": "https://brightdata.com/",
        "enabled_by_default": False,
        "compliance_notes": "Disabled placeholder pending compliance review and provider-specific tests.",
    },
    {
        "name": "Zillow",
        "kind": "web",
        "adapter_key": "zillow_html",
        "status": "disabled",
        "base_url": "https://www.zillow.com/",
        "enabled_by_default": False,
        "compliance_notes": "Disabled pending compliant access path.",
    },
    {
        "name": "Redfin",
        "kind": "web",
        "adapter_key": "redfin_unofficial",
        "status": "disabled",
        "base_url": "https://www.redfin.com/",
        "enabled_by_default": False,
        "compliance_notes": "Disabled pending approved or licensed access.",
    },
    {
        "name": "Realtor.com",
        "kind": "web",
        "adapter_key": "realtor_html",
        "status": "disabled",
        "base_url": "https://www.realtor.com/",
        "enabled_by_default": False,
        "compliance_notes": "Disabled pending explicit permission.",
    },
    {
        "name": "Apartments.com",
        "kind": "web",
        "adapter_key": "apartments_reference",
        "status": "disabled",
        "base_url": "https://www.apartments.com/",
        "enabled_by_default": False,
        "compliance_notes": "Use only through approved workflows or manual imports.",
    },
    {
        "name": "HotPads",
        "kind": "web",
        "adapter_key": "hotpads_reference",
        "status": "disabled",
        "base_url": "https://www.hotpads.com/",
        "enabled_by_default": False,
        "compliance_notes": "Use only through approved workflows or manual imports.",
    },
    {
        "name": "Craigslist",
        "kind": "web",
        "adapter_key": "craigslist_reference",
        "status": "disabled",
        "base_url": "https://www.craigslist.org/",
        "enabled_by_default": False,
        "compliance_notes": "Reference/manual-only unless explicit permission is reviewed.",
    },
    {
        "name": "Facebook Marketplace",
        "kind": "web",
        "adapter_key": "facebook_marketplace_reference",
        "status": "disabled",
        "base_url": "https://www.facebook.com/marketplace/",
        "enabled_by_default": False,
        "compliance_notes": "Reference/manual-only unless Meta permission is reviewed.",
    },
]


def ensure_sources(db: Session) -> None:
    for entry in SOURCE_CATALOG:
        existing = db.scalar(select(Source).where(Source.name == entry["name"]))
        if existing:
            for field, value in entry.items():
                setattr(existing, field, value)
        else:
            db.add(Source(**entry))
    db.commit()


def ensure_default_criteria(db: Session) -> SearchCriteria:
    criteria = db.scalar(select(SearchCriteria).where(SearchCriteria.is_active.is_(True)))
    if criteria:
        return criteria

    criteria = SearchCriteria(**DEFAULT_SEARCH_CRITERIA)
    db.add(criteria)
    db.commit()
    db.refresh(criteria)
    return criteria


def seed_demo_data(db: Session) -> None:
    ensure_sources(db)
    criteria = ensure_default_criteria(db)

    if db.scalar(select(Listing.id).limit(1)):
        sync_scores(db, criteria)
        return

    manual_source = db.scalar(select(Source).where(Source.name == "Manual Import"))
    if manual_source is None:
        raise RuntimeError("Manual Import source is required for seed data.")

    import_run = ImportRun(
        source_id=manual_source.id,
        adapter_key="seed_demo",
        run_mode="seed",
        status="completed",
        records_seen=8,
        records_created=8,
        started_at=datetime.utcnow(),
        finished_at=datetime.utcnow(),
        warnings=["Seed data uses demo content for UI and scoring only."],
    )
    db.add(import_run)
    db.flush()

    demo_listings = [
        {
            "title": "Northwood Backyard Lease",
            "address_line1": "118 Demo Ridge",
            "city": "Irvine",
            "neighborhood": "Northwood",
            "county": "Orange County",
            "state": "CA",
            "postal_code": "92620",
            "price": Decimal("4650.00"),
            "bedrooms": 3,
            "bathrooms": 2.5,
            "square_feet": 1840,
            "lot_size_sqft": 3400,
            "has_backyard": True,
            "has_garage": True,
            "garage_spaces": 2,
            "pets_allowed": True,
            "watchlist_status": "shortlist",
            "property_type": "townhome",
            "listing_url": "https://www.zillow.com/",
            "description": "Fresh paint, enclosed backyard, attached two-car garage, near schools and parks.",
            "feature_tags": ["backyard", "garage", "pets", "shortlist"],
            "confidence": 0.88,
            "listed_at": datetime(2026, 5, 1),
            "last_seen_at": datetime(2026, 5, 5),
            "raw_payload": {"seed": True, "source_hint": "zillow_demo"},
        },
        {
            "title": "Tustin Ranch Family Lease",
            "address_line1": "44 Canary Glen",
            "city": "Tustin",
            "neighborhood": "Tustin Ranch",
            "county": "Orange County",
            "state": "CA",
            "postal_code": "92782",
            "price": Decimal("4350.00"),
            "bedrooms": 3,
            "bathrooms": 2.0,
            "square_feet": 1710,
            "lot_size_sqft": 3200,
            "has_backyard": True,
            "has_garage": True,
            "garage_spaces": 2,
            "pets_allowed": False,
            "watchlist_status": "review",
            "property_type": "single_family",
            "listing_url": "https://www.redfin.com/",
            "description": "Competitive price for Tustin Ranch with yard space and attached garage.",
            "feature_tags": ["backyard", "garage", "value"],
            "confidence": 0.82,
            "listed_at": datetime(2026, 4, 28),
            "last_seen_at": datetime(2026, 5, 5),
            "raw_payload": {"seed": True, "source_hint": "redfin_demo"},
        },
        {
            "title": "Orange Hills Detached Home",
            "address_line1": "809 Santiago Crest",
            "city": "Orange",
            "neighborhood": "Orange Hills",
            "county": "Orange County",
            "state": "CA",
            "postal_code": "92867",
            "price": Decimal("5250.00"),
            "bedrooms": 4,
            "bathrooms": 3.0,
            "square_feet": 2235,
            "lot_size_sqft": 5100,
            "has_backyard": True,
            "has_garage": True,
            "garage_spaces": 2,
            "pets_allowed": True,
            "watchlist_status": "tour",
            "property_type": "single_family",
            "listing_url": "https://www.realtor.com/",
            "description": "Larger footprint with strong family fit, but at a premium monthly rate.",
            "feature_tags": ["backyard", "garage", "spacious", "tour"],
            "confidence": 0.84,
            "listed_at": datetime(2026, 4, 30),
            "last_seen_at": datetime(2026, 5, 4),
            "raw_payload": {"seed": True, "source_hint": "realtor_demo"},
        },
        {
            "title": "Mission Viejo Patio Lease",
            "address_line1": "17 Cedarwind",
            "city": "Mission Viejo",
            "neighborhood": "Pacific Hills",
            "county": "Orange County",
            "state": "CA",
            "postal_code": "92692",
            "price": Decimal("4195.00"),
            "bedrooms": 3,
            "bathrooms": 2.5,
            "square_feet": 1685,
            "lot_size_sqft": 2900,
            "has_backyard": True,
            "has_garage": True,
            "garage_spaces": 2,
            "pets_allowed": True,
            "watchlist_status": "shortlist",
            "property_type": "single_family",
            "listing_url": "https://www.apartments.com/",
            "description": "Best pure price fit in the seed set with a small but usable backyard.",
            "feature_tags": ["backyard", "garage", "pets", "value"],
            "confidence": 0.78,
            "listed_at": datetime(2026, 5, 3),
            "last_seen_at": datetime(2026, 5, 5),
            "raw_payload": {"seed": True, "source_hint": "apartments_demo"},
        },
        {
            "title": "Costa Mesa Duplex with Yard",
            "address_line1": "601 Harbor Oak",
            "city": "Costa Mesa",
            "neighborhood": "Mesa Verde",
            "county": "Orange County",
            "state": "CA",
            "postal_code": "92626",
            "price": Decimal("3995.00"),
            "bedrooms": 3,
            "bathrooms": 2.0,
            "square_feet": 1490,
            "lot_size_sqft": 2600,
            "has_backyard": True,
            "has_garage": False,
            "garage_spaces": 0,
            "pets_allowed": True,
            "watchlist_status": "review",
            "property_type": "duplex",
            "listing_url": "https://www.hotpads.com/",
            "description": "Great price, but only driveway parking and no garage.",
            "feature_tags": ["backyard", "pets", "budget"],
            "confidence": 0.72,
            "listed_at": datetime(2026, 4, 24),
            "last_seen_at": datetime(2026, 5, 2),
            "raw_payload": {"seed": True, "source_hint": "hotpads_demo"},
        },
        {
            "title": "Anaheim Hills Split-Level",
            "address_line1": "95 Silver Mesa",
            "city": "Anaheim",
            "neighborhood": "Anaheim Hills",
            "county": "Orange County",
            "state": "CA",
            "postal_code": "92808",
            "price": Decimal("4795.00"),
            "bedrooms": 4,
            "bathrooms": 2.5,
            "square_feet": 2085,
            "lot_size_sqft": 4200,
            "has_backyard": True,
            "has_garage": True,
            "garage_spaces": 3,
            "pets_allowed": True,
            "watchlist_status": "review",
            "property_type": "single_family",
            "listing_url": "https://example.com/demo/csv-import/anaheim-hills",
            "description": "Strong family footprint and 3-car garage, slightly farther east for some commutes.",
            "feature_tags": ["backyard", "garage", "spacious", "csv"],
            "confidence": 0.76,
            "listed_at": datetime(2026, 4, 26),
            "last_seen_at": datetime(2026, 5, 4),
            "raw_payload": {"seed": True, "source_hint": "csv_demo"},
        },
        {
            "title": "Laguna Niguel Courtyard Townhome",
            "address_line1": "233 Sea Whisper",
            "city": "Laguna Niguel",
            "neighborhood": "Marina Hills",
            "county": "Orange County",
            "state": "CA",
            "postal_code": "92677",
            "price": Decimal("4480.00"),
            "bedrooms": 3,
            "bathrooms": 2.5,
            "square_feet": 1770,
            "lot_size_sqft": 3000,
            "has_backyard": False,
            "has_garage": True,
            "garage_spaces": 2,
            "pets_allowed": True,
            "watchlist_status": "review",
            "property_type": "townhome",
            "listing_url": "https://example.com/demo/manual/laguna-niguel-courtyard",
            "description": "Excellent garage and layout, but only a courtyard instead of a true backyard.",
            "feature_tags": ["garage", "pets", "manual"],
            "confidence": 0.69,
            "listed_at": datetime(2026, 5, 2),
            "last_seen_at": datetime(2026, 5, 5),
            "raw_payload": {"seed": True, "source_hint": "manual_demo"},
        },
        {
            "title": "Lake Forest Cul-de-Sac Lease",
            "address_line1": "12 Poppy Arbor",
            "city": "Lake Forest",
            "neighborhood": "Foothill Ranch",
            "county": "Orange County",
            "state": "CA",
            "postal_code": "92610",
            "price": Decimal("4890.00"),
            "bedrooms": 4,
            "bathrooms": 3.0,
            "square_feet": 2165,
            "lot_size_sqft": 4300,
            "has_backyard": True,
            "has_garage": True,
            "garage_spaces": 2,
            "pets_allowed": False,
            "watchlist_status": "review",
            "property_type": "single_family",
            "listing_url": "https://example.com/demo/public-feed/lake-forest",
            "description": "High-confidence normalized demo listing with room to grow and a family-friendly layout.",
            "feature_tags": ["backyard", "garage", "spacious", "public_feed"],
            "confidence": 0.91,
            "listed_at": datetime(2026, 4, 29),
            "last_seen_at": datetime(2026, 5, 5),
            "raw_payload": {"seed": True, "source_hint": "public_feed_demo"},
        },
    ]

    source_lookup = {
        "https://www.zillow.com/": "Zillow",
        "https://www.redfin.com/": "Redfin",
        "https://www.realtor.com/": "Realtor.com",
        "https://www.apartments.com/": "Apartments.com",
        "https://www.hotpads.com/": "HotPads",
    }

    for row in demo_listings:
        source_name = source_lookup.get(row["listing_url"], "Manual Import")
        source = db.scalar(select(Source).where(Source.name == source_name))
        row["source_url"] = row["listing_url"]
        row["source_domain"] = None
        row["source_type"] = "seed"
        row["source_confidence"] = row["confidence"]
        row["source_listing_id"] = row.get("external_id")
        row["backyard_status"] = "yes" if row["has_backyard"] else "no"
        row["garage_status"] = "yes" if row["has_garage"] else "no"
        row["backyard_evidence"] = row["description"]
        row["garage_evidence"] = row["description"]
        row["parking_details"] = f"{row['garage_spaces'] or 0} garage spaces" if row.get("garage_spaces") else "Parking details unverified"
        row["pet_policy"] = "Pets allowed" if row["pets_allowed"] else "Pets not verified or not allowed"
        row["first_seen_at"] = row["listed_at"]
        row["imported_at"] = datetime.utcnow()
        row["listing_status"] = "active"
        row["raw_text"] = row["description"]
        listing = Listing(
            source_id=source.id if source else manual_source.id,
            import_run_id=import_run.id,
            **row,
        )
        db.add(listing)
        db.flush()

        db.add(
            ListingNote(
                listing_id=listing.id,
                author="seed",
                note="Demo listing seeded for immediate dashboard use.",
            )
        )
        db.add(
            WatchlistEntry(
                listing_id=listing.id,
                status=row["watchlist_status"],
                priority="medium" if row["watchlist_status"] == "review" else "high",
                reason="Seeded initial triage state.",
            )
        )

    db.commit()
    sync_scores(db, criteria)


def sync_scores(db: Session, criteria: SearchCriteria | None = None) -> None:
    criteria = criteria or ensure_default_criteria(db)
    listings = db.scalars(
        select(Listing)
        .options(selectinload(Listing.source), selectinload(Listing.notes))
        .where(Listing.is_active.is_(True))
    ).all()

    db.execute(delete(ListingScore).where(ListingScore.criteria_id == criteria.id))
    db.flush()

    for listing in listings:
        payload = compute_listing_score(listing, criteria)
        listing.match_score = payload["hard_criteria_score"]
        listing.deal_score = payload["deal_score"]
        listing.confidence_score = payload["confidence_score"]
        if listing.decision_status == "new" and payload["needs_review_badges"]:
            listing.decision_status = "needs_review"
            listing.next_action = listing.next_action or "; ".join(payload["next_actions"][:2])
            listing.priority = "high" if "Possibly good deal" in payload["needs_review_badges"] else "medium"
        score_payload = {
            "total_score": payload["total_score"],
            "price_score": payload["price_score"],
            "space_score": payload["space_score"],
            "location_score": payload["location_score"],
            "feature_score": payload["feature_score"],
            "freshness_score": payload["freshness_score"],
            "confidence_score": payload["confidence_score"],
            "hard_criteria_score": payload["hard_criteria_score"],
            "deal_score": payload["deal_score"],
            "data_completeness_score": payload["data_completeness_score"],
            "source_reliability_score": payload["source_reliability_score"],
            "explanation": payload["explanation"],
        }
        db.add(
            ListingScore(
                listing_id=listing.id,
                criteria_id=criteria.id,
                **score_payload,
            )
        )

    db.commit()
    logger.info("Scoring recalculated for %s active listings", len(listings))


def get_active_criteria(db: Session) -> SearchCriteria:
    return ensure_default_criteria(db)


def update_search_criteria(db: Session, payload: SearchCriteriaUpdate) -> SearchCriteria:
    criteria = ensure_default_criteria(db)
    for field, value in payload.model_dump().items():
        setattr(criteria, field, value)
    criteria.is_active = True
    db.add(criteria)
    db.commit()
    db.refresh(criteria)
    sync_scores(db, criteria)
    return criteria


def _score_lookup(db: Session, criteria_id: int) -> dict[int, ListingScore]:
    scores = db.scalars(select(ListingScore).where(ListingScore.criteria_id == criteria_id)).all()
    return {score.listing_id: score for score in scores}


def serialize_score(score: ListingScore | None) -> ScoreBreakdownRead | None:
    if score is None:
        return None
    explanation = score.explanation or {}
    return ScoreBreakdownRead(
        listing_id=score.listing_id,
        criteria_id=score.criteria_id,
        total_score=score.total_score,
        price_score=score.price_score,
        space_score=score.space_score,
        location_score=score.location_score,
        feature_score=score.feature_score,
        freshness_score=score.freshness_score,
        confidence_score=score.confidence_score,
        hard_criteria_score=score.hard_criteria_score,
        match_score=explanation.get("match_score", score.hard_criteria_score),
        deal_score=score.deal_score,
        data_completeness_score=score.data_completeness_score,
        completeness_score=explanation.get("completeness_score", score.data_completeness_score),
        source_reliability_score=score.source_reliability_score,
        overall_score=explanation.get("overall_score", score.total_score),
        price_per_bedroom=explanation.get("price_per_bedroom"),
        price_per_sqft=explanation.get("price_per_sqft"),
        benchmark_city=explanation.get("benchmark_context", {}).get("benchmark_city"),
        benchmark_used=bool(explanation.get("benchmark_context", {}).get("benchmark_used")),
        benchmark_used_fallback=bool(explanation.get("benchmark_context", {}).get("benchmark_used_fallback")),
        benchmark_confidence=explanation.get("benchmark_context", {}).get("benchmark_confidence"),
        benchmark_source_type=explanation.get("benchmark_context", {}).get("benchmark_source_type"),
        median_rent_3br=explanation.get("benchmark_context", {}).get("median_rent_3br"),
        typical_low_3br=explanation.get("benchmark_context", {}).get("typical_low_3br"),
        typical_high_3br=explanation.get("benchmark_context", {}).get("typical_high_3br"),
        rent_delta_vs_median=explanation.get("benchmark_context", {}).get("rent_delta_vs_median"),
        rent_delta_percent=explanation.get("benchmark_context", {}).get("rent_delta_percent"),
        price_per_sqft_delta=explanation.get("benchmark_context", {}).get("price_per_sqft_delta"),
        market_label=explanation.get("benchmark_context", {}).get("market_label"),
        benchmark_notes=explanation.get("benchmark_context", {}).get("benchmark_notes"),
        benchmark_sources=explanation.get("benchmark_context", {}).get("benchmark_sources", []),
        reasons=explanation.get("reasons", []),
        warnings=explanation.get("warnings", []),
        next_actions=explanation.get("next_actions", []),
        needs_review_badges=explanation.get("needs_review_badges", []),
        explanation=score.explanation,
        computed_at=score.computed_at,
    )


def serialize_listing(listing: Listing, score: ListingScore | None) -> ListingRead:
    return ListingRead(
        id=listing.id,
        title=listing.title,
        address=listing.address_line1,
        address_line1=listing.address_line1,
        city=listing.city,
        neighborhood=listing.neighborhood,
        county=listing.county,
        state=listing.state,
        zip=listing.postal_code,
        postal_code=listing.postal_code,
        latitude=listing.latitude,
        longitude=listing.longitude,
        price_monthly=float(listing.price),
        price=float(listing.price),
        bedrooms=listing.bedrooms,
        bathrooms=listing.bathrooms,
        square_feet=listing.square_feet,
        lot_size=listing.lot_size_sqft,
        lot_size_sqft=listing.lot_size_sqft,
        has_backyard=listing.has_backyard,
        backyard_status=listing.backyard_status,
        backyard_evidence=listing.backyard_evidence,
        has_garage=listing.has_garage,
        garage_status=listing.garage_status,
        garage_evidence=listing.garage_evidence,
        garage_spaces=listing.garage_spaces,
        parking_details=listing.parking_details,
        pets_allowed=listing.pets_allowed,
        pet_policy=listing.pet_policy,
        laundry=listing.laundry,
        air_conditioning=listing.air_conditioning,
        listing_status=listing.listing_status,
        decision_status=listing.decision_status,
        decision_reason=listing.decision_reason,
        priority=listing.priority,
        next_action=listing.next_action,
        next_action_due_date=listing.next_action_due_date,
        contact_name=listing.contact_name,
        contact_phone=listing.contact_phone,
        contact_email=listing.contact_email,
        tour_date=listing.tour_date,
        user_rating=listing.user_rating,
        private_notes=listing.private_notes,
        watchlist_status=listing.watchlist_status,
        property_type=listing.property_type,
        source_url=listing.source_url or listing.listing_url,
        listing_url=listing.listing_url,
        source_domain=listing.source_domain,
        source_listing_id=listing.source_listing_id or listing.external_id,
        discovery_run_id=listing.discovery_run_id,
        image_url=listing.image_url,
        description=listing.description,
        raw_text=listing.raw_text,
        raw_payload_json=listing.raw_payload,
        feature_tags=listing.feature_tags,
        confidence=listing.confidence,
        source_confidence=listing.source_confidence,
        match_score=listing.match_score,
        deal_score=listing.deal_score,
        confidence_score=listing.confidence_score,
        first_seen_at=listing.first_seen_at,
        listed_at=listing.listed_at,
        last_seen_at=listing.last_seen_at,
        imported_at=listing.imported_at,
        updated_at=listing.updated_at,
        source_name=listing.source.name,
        source_kind=listing.source.kind,
        source_type=listing.source_type,
        notes=list(listing.notes),
        score=serialize_score(score),
        score_breakdown=serialize_score(score),
    )


def get_listings(db: Session, filters: ListingFilterParams) -> list[ListingRead]:
    criteria = ensure_default_criteria(db)
    score_map = _score_lookup(db, criteria.id)
    query = (
        select(Listing)
        .options(selectinload(Listing.source), selectinload(Listing.notes))
        .where(Listing.is_active.is_(True))
    )

    if filters.county:
        query = query.where(Listing.county == filters.county)
    if filters.city:
        query = query.where(Listing.city == filters.city)
    if filters.min_bedrooms is not None:
        query = query.where(Listing.bedrooms >= filters.min_bedrooms)
    if filters.max_price is not None:
        query = query.where(Listing.price <= filters.max_price)
    if filters.source_name:
        query = query.join(Listing.source).where(Source.name == filters.source_name)
    if filters.watchlist_status:
        query = query.where(Listing.watchlist_status == filters.watchlist_status)
    if filters.decision_status:
        query = query.where(Listing.decision_status == filters.decision_status)
    if filters.needs_review:
        query = query.where(Listing.decision_status == "needs_review")
    if filters.discovery_only:
        query = query.where(Listing.discovery_run_id.is_not(None))
    if filters.new_from_discovery:
        query = query.where(Listing.discovery_run_id.is_not(None), Listing.decision_status == "new")
    if filters.needs_review_from_discovery:
        query = query.where(
            Listing.discovery_run_id.is_not(None),
            or_(Listing.decision_status == "needs_review", Listing.listing_status == "needs_manual_review"),
        )
    if filters.backyard == "yes_unknown":
        query = query.where(Listing.backyard_status.in_(["yes", "unknown"]))
    elif filters.backyard:
        query = query.where(Listing.backyard_status == filters.backyard)
    if filters.garage == "yes_unknown":
        query = query.where(Listing.garage_status.in_(["yes", "unknown"]))
    elif filters.garage:
        query = query.where(Listing.garage_status == filters.garage)
    if filters.require_backyard:
        query = query.where(Listing.backyard_status == "yes")
    if filters.require_garage:
        query = query.where(Listing.garage_status == "yes")
    if filters.pets_required:
        query = query.where(Listing.pets_allowed.is_(True))

    listings = db.scalars(query).all()
    results = [serialize_listing(listing, score_map.get(listing.id)) for listing in listings]

    if filters.sort_by == "price_asc":
        results.sort(key=lambda item: item.price)
    elif filters.sort_by == "space_desc":
        results.sort(key=lambda item: (item.square_feet or 0, item.bedrooms), reverse=True)
    elif filters.sort_by == "newest":
        results.sort(key=lambda item: item.listed_at or datetime.min, reverse=True)
    elif filters.sort_by == "confidence":
        results.sort(key=lambda item: item.confidence_score, reverse=True)
    elif filters.sort_by == "match_score":
        results.sort(key=lambda item: item.match_score, reverse=True)
    elif filters.sort_by == "deal_score":
        results.sort(key=lambda item: item.deal_score, reverse=True)
    elif filters.sort_by == "best_below_market":
        results.sort(
            key=lambda item: (
                item.score.rent_delta_percent if item.score and item.score.rent_delta_percent is not None else 999,
                -(item.score.deal_score if item.score else 0),
            )
        )
    elif filters.sort_by == "completeness":
        results.sort(key=lambda item: item.score.completeness_score if item.score else 0, reverse=True)
    elif filters.sort_by == "overall_score":
        results.sort(key=lambda item: item.score.overall_score if item.score else 0, reverse=True)
    else:
        results.sort(key=lambda item: item.score.total_score if item.score else 0, reverse=True)

    return results


def _source_for_normalized(db: Session, listing: NormalizedListing) -> Source:
    ensure_sources(db)
    source = db.scalar(select(Source).where(Source.name == listing.provenance.source_name))
    if source is None:
        source = Source(
            name=listing.provenance.source_name,
            kind=listing.provenance.source_type,
            adapter_key=listing.provenance.source_type,
            status="active",
            base_url=None,
            enabled_by_default=True,
            compliance_notes="Created from safe user-provided ingestion.",
        )
        db.add(source)
        db.flush()
    return source


def _persist_normalized_listing(
    db: Session,
    normalized: NormalizedListing,
    import_run: ImportRun,
) -> Listing:
    now = datetime.utcnow()
    listing_url = normalized.provenance.source_url
    confidence = normalized.provenance.source_confidence
    has_backyard = normalized.backyard_status == "yes"
    has_garage = normalized.garage_status == "yes"
    pets_allowed = None
    if normalized.pet_policy:
        lowered_pet_policy = normalized.pet_policy.lower()
        if any(term in lowered_pet_policy for term in ["allowed", "ok", "dog", "cat", "pet friendly"]):
            pets_allowed = True
        if any(term in lowered_pet_policy for term in ["no pets", "not allowed"]):
            pets_allowed = False

    listing = Listing(
        source_id=import_run.source_id,
        import_run_id=import_run.id,
        external_id=normalized.provenance.source_listing_id,
        source_listing_id=normalized.provenance.source_listing_id,
        title=normalized.title,
        address_line1=normalized.address,
        city=normalized.city,
        neighborhood=normalized.neighborhood,
        county=normalized.county,
        state=normalized.state,
        postal_code=normalized.zip,
        latitude=normalized.latitude,
        longitude=normalized.longitude,
        price=Decimal(str(normalized.price_monthly)),
        bedrooms=normalized.bedrooms,
        bathrooms=normalized.bathrooms,
        square_feet=normalized.square_feet,
        lot_size_sqft=normalized.lot_size,
        has_backyard=has_backyard,
        backyard_status=normalized.backyard_status,
        backyard_evidence=normalized.backyard_evidence,
        has_garage=has_garage,
        garage_status=normalized.garage_status,
        garage_evidence=normalized.garage_evidence,
        garage_spaces=None,
        parking_details=normalized.parking_details,
        pets_allowed=pets_allowed,
        pet_policy=normalized.pet_policy,
        laundry=normalized.laundry,
        air_conditioning=normalized.air_conditioning,
        watchlist_status=normalized.watchlist_status,
        property_type=normalized.property_type,
        listing_url=listing_url,
        source_url=listing_url,
        source_domain=normalized.provenance.source_domain,
        source_type=normalized.provenance.source_type,
        description=normalized.description,
        raw_text=normalized.provenance.raw_text,
        raw_payload=normalized.provenance.raw_payload_json,
        feature_tags=normalized.feature_tags,
        confidence=confidence,
        source_confidence=confidence,
        first_seen_at=normalized.provenance.imported_at,
        listed_at=normalized.provenance.imported_at,
        last_seen_at=normalized.provenance.imported_at,
        imported_at=normalized.provenance.imported_at,
        listing_status=normalized.listing_status,
        decision_status="needs_review" if normalized.listing_status == "needs_manual_review" else "new",
        next_action="Verify imported listing details" if normalized.listing_status == "needs_manual_review" else None,
        is_active=True,
    )
    db.add(listing)
    db.flush()

    if normalized.notes:
        db.add(ListingNote(listing_id=listing.id, author="user", note=normalized.notes))

    db.add(
        WatchlistEntry(
            listing_id=listing.id,
            status=listing.watchlist_status,
            priority="high" if listing.watchlist_status in {"shortlist", "tour"} else "medium",
            reason=f"Created by {normalized.provenance.source_type} import.",
        )
    )
    listing.updated_at = now
    return listing


def _clip_payload_size(payload: BrowserClipRequest) -> int:
    return sum(
        len(str(value or ""))
        for value in [
            payload.source_url,
            payload.page_title,
            payload.selected_text,
            payload.page_text,
            payload.source_domain,
            payload.user_notes,
        ]
    )


def _duplicate_key(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def _find_exact_source_duplicate(
    db: Session,
    source_url: str | None,
    source_listing_id: str | None = None,
) -> Listing | None:
    if source_url:
        duplicate = db.scalar(
            select(Listing)
            .options(selectinload(Listing.source), selectinload(Listing.notes))
            .where(
                Listing.is_active.is_(True),
                or_(Listing.source_url == source_url, Listing.listing_url == source_url),
            )
            .order_by(Listing.id.asc())
            .limit(1)
        )
        if duplicate:
            return duplicate
    if not source_listing_id:
        return None
    return db.scalar(
        select(Listing)
        .options(selectinload(Listing.source), selectinload(Listing.notes))
        .where(
            Listing.is_active.is_(True),
            or_(Listing.source_listing_id == source_listing_id, Listing.external_id == source_listing_id),
        )
        .order_by(Listing.id.asc())
        .limit(1)
    )


def _find_possible_duplicates(db: Session, normalized: NormalizedListing) -> list[Listing]:
    normalized_address = _duplicate_key(normalized.address)
    normalized_title = _duplicate_key(normalized.title)
    normalized_city = _duplicate_key(normalized.city)
    possible: list[Listing] = []

    existing_listings = db.scalars(
        select(Listing)
        .options(selectinload(Listing.source), selectinload(Listing.notes))
        .where(Listing.is_active.is_(True))
    ).all()

    for existing in existing_listings:
        same_address = bool(normalized_address and _duplicate_key(existing.address_line1) == normalized_address)
        same_title_city_price = (
            bool(normalized_title and normalized_city and normalized.price_monthly > 0)
            and _duplicate_key(existing.title) == normalized_title
            and _duplicate_key(existing.city) == normalized_city
            and abs(float(existing.price) - normalized.price_monthly) <= 1
        )
        same_address_price = (
            bool(normalized_address and normalized.price_monthly > 0)
            and _duplicate_key(existing.address_line1) == normalized_address
            and abs(float(existing.price) - normalized.price_monthly) <= 1
        )
        if same_address or same_title_city_price or same_address_price:
            possible.append(existing)

    return possible


def _apply_normalized_update(
    db: Session,
    listing: Listing,
    normalized: NormalizedListing,
    import_run: ImportRun,
) -> Listing:
    now = datetime.utcnow()
    listing.source_id = import_run.source_id
    listing.import_run_id = import_run.id
    listing.external_id = normalized.provenance.source_listing_id or listing.external_id
    listing.source_listing_id = normalized.provenance.source_listing_id or listing.source_listing_id
    listing.title = normalized.title or listing.title
    listing.address_line1 = normalized.address or listing.address_line1
    if normalized.city and normalized.city != "Unknown":
        listing.city = normalized.city
    listing.neighborhood = normalized.neighborhood or listing.neighborhood
    listing.county = normalized.county or listing.county
    listing.state = normalized.state or listing.state
    listing.postal_code = normalized.zip or listing.postal_code
    listing.latitude = normalized.latitude or listing.latitude
    listing.longitude = normalized.longitude or listing.longitude
    if normalized.price_monthly > 0:
        listing.price = Decimal(str(normalized.price_monthly))
    if normalized.bedrooms > 0:
        listing.bedrooms = normalized.bedrooms
    if normalized.bathrooms > 0:
        listing.bathrooms = normalized.bathrooms
    listing.square_feet = normalized.square_feet or listing.square_feet
    listing.lot_size_sqft = normalized.lot_size or listing.lot_size_sqft
    if normalized.backyard_status != "unknown":
        listing.backyard_status = normalized.backyard_status
        listing.has_backyard = normalized.backyard_status == "yes"
        listing.backyard_evidence = normalized.backyard_evidence or listing.backyard_evidence
    if normalized.garage_status != "unknown":
        listing.garage_status = normalized.garage_status
        listing.has_garage = normalized.garage_status == "yes"
        listing.garage_evidence = normalized.garage_evidence or listing.garage_evidence
    listing.parking_details = normalized.parking_details or listing.parking_details
    listing.pet_policy = normalized.pet_policy or listing.pet_policy
    listing.laundry = normalized.laundry or listing.laundry
    listing.air_conditioning = normalized.air_conditioning or listing.air_conditioning
    listing.property_type = normalized.property_type if normalized.property_type != "unknown" else listing.property_type
    listing.listing_url = normalized.provenance.source_url or listing.listing_url
    listing.source_url = normalized.provenance.source_url or listing.source_url
    listing.source_domain = normalized.provenance.source_domain or listing.source_domain
    listing.source_type = normalized.provenance.source_type
    listing.description = normalized.description or listing.description
    listing.raw_text = normalized.provenance.raw_text or listing.raw_text
    listing.raw_payload = {
        **(listing.raw_payload or {}),
        **normalized.provenance.raw_payload_json,
        "duplicate_update": True,
    }
    listing.feature_tags = list(dict.fromkeys((listing.feature_tags or []) + normalized.feature_tags))
    listing.confidence = normalized.provenance.source_confidence or listing.confidence
    listing.source_confidence = normalized.provenance.source_confidence or listing.source_confidence
    listing.last_seen_at = now
    listing.imported_at = normalized.provenance.imported_at
    listing.updated_at = now

    if normalized.pet_policy:
        lowered_pet_policy = normalized.pet_policy.lower()
        if any(term in lowered_pet_policy for term in ["allowed", "ok", "dog", "cat", "pet friendly"]):
            listing.pets_allowed = True
        if any(term in lowered_pet_policy for term in ["no pets", "not allowed"]):
            listing.pets_allowed = False

    if normalized.notes:
        db.add(ListingNote(listing_id=listing.id, author="user", note=normalized.notes))

    db.add(listing)
    return listing


def _create_import_run(db: Session, source: Source, adapter_key: str, run_mode: str, result: IngestionResult) -> ImportRun:
    import_run = ImportRun(
        source_id=source.id,
        adapter_key=adapter_key,
        run_mode=run_mode,
        status="completed" if not result.errors else "completed_with_errors",
        records_seen=result.rows_received,
        records_created=result.rows_imported,
        records_updated=0,
        started_at=datetime.utcnow(),
        finished_at=datetime.utcnow(),
        warnings=result.warnings,
        error_text="; ".join(error["message"] for error in result.errors) if result.errors else None,
    )
    db.add(import_run)
    db.flush()
    return import_run


def _persist_ingestion_result(
    db: Session,
    result: IngestionResult,
    *,
    adapter_key: str,
    run_mode: str,
) -> list[ListingRead]:
    criteria = ensure_default_criteria(db)
    created: list[Listing] = []
    if result.listings:
        source = _source_for_normalized(db, result.listings[0])
    else:
        source = db.scalar(select(Source).where(Source.name == "Manual Import"))
        if source is None:
            ensure_sources(db)
            source = db.scalar(select(Source).where(Source.name == "Manual Import"))

    import_run = _create_import_run(db, source, adapter_key, run_mode, result)

    for normalized in result.listings:
        if normalized.provenance.source_name != source.name:
            source = _source_for_normalized(db, normalized)
            import_run.source_id = source.id
        created.append(_persist_normalized_listing(db, normalized, import_run))

    db.commit()
    sync_scores(db, criteria)

    score_map = _score_lookup(db, criteria.id)
    refreshed = db.scalars(
        select(Listing)
        .options(selectinload(Listing.source), selectinload(Listing.notes))
        .where(Listing.id.in_([listing.id for listing in created]))
    ).all()
    return [serialize_listing(listing, score_map.get(listing.id)) for listing in refreshed]


def persist_discovery_result(
    db: Session,
    result: IngestionResult,
    *,
    adapter_key: str,
    run_mode: str = "automatic_discovery",
) -> dict:
    criteria = ensure_default_criteria(db)
    if result.listings:
        source = _source_for_normalized(db, result.listings[0])
    else:
        ensure_sources(db)
        source = db.scalar(select(Source).where(Source.name == "Manual Import"))

    import_run = _create_import_run(db, source, adapter_key, run_mode, result)
    warnings = list(result.warnings)
    created: list[Listing] = []
    records_created = 0
    records_updated = 0
    possible_duplicate_count = 0

    for normalized in result.listings:
        if normalized.provenance.source_name != source.name:
            source = _source_for_normalized(db, normalized)
            import_run.source_id = source.id

        exact_duplicate = _find_exact_source_duplicate(
            db,
            normalized.provenance.source_url,
            normalized.provenance.source_listing_id,
        )
        if exact_duplicate:
            records_updated += 1
            warnings.append(
                f"Exact source URL or source listing ID matched listing #{exact_duplicate.id}; updated existing listing instead of creating a duplicate."
            )
            listing = _apply_normalized_update(db, exact_duplicate, normalized, import_run)
            created.append(listing)
            continue

        possible_duplicates = _find_possible_duplicates(db, normalized)
        if possible_duplicates:
            possible_duplicate_count += 1
            duplicate_ids = [item.id for item in possible_duplicates]
            warnings.append(f"Possible duplicate detected by address, address/price, or title/city/price: listing IDs {duplicate_ids}.")
            normalized.provenance.raw_payload_json = {
                **normalized.provenance.raw_payload_json,
                "possible_duplicate_listing_ids": duplicate_ids,
            }
            normalized.feature_tags = list(dict.fromkeys(normalized.feature_tags + ["possible_duplicate"]))

        listing = _persist_normalized_listing(db, normalized, import_run)
        records_created += 1
        if possible_duplicates:
            listing.decision_status = "needs_review"
            listing.priority = "high"
            listing.next_action = "Review possible duplicate before contacting or touring."
            listing.raw_payload = {
                **(listing.raw_payload or {}),
                "possible_duplicate_listing_ids": [item.id for item in possible_duplicates],
            }
        created.append(listing)

    import_run.records_created = records_created
    import_run.records_updated = records_updated
    import_run.records_seen = result.rows_received
    import_run.warnings = warnings
    db.commit()
    sync_scores(db, criteria)

    listing_ids = [listing.id for listing in created]
    score_map = _score_lookup(db, criteria.id)
    refreshed = []
    if listing_ids:
        refreshed = db.scalars(
            select(Listing)
            .options(selectinload(Listing.source), selectinload(Listing.notes))
            .where(Listing.id.in_(listing_ids))
        ).all()

    return {
        "import_run_id": import_run.id,
        "rows_received": result.rows_received,
        "rows_imported": result.rows_imported,
        "rows_skipped": result.rows_skipped,
        "records_created": records_created,
        "records_updated": records_updated,
        "possible_duplicates": possible_duplicate_count,
        "listing_ids": listing_ids,
        "warnings": warnings,
        "errors": result.errors,
        "listings": [serialize_listing(listing, score_map.get(listing.id)) for listing in refreshed],
    }


def create_manual_listing(db: Session, payload: ManualListingCreate) -> ListingRead:
    result = ManualEntryAdapter().ingest(payload)
    logger.info("Manual listing import requested for city=%s", payload.city)
    return _persist_ingestion_result(db, result, adapter_key="manual", run_mode="manual_entry")[0]


def create_paste_import(db: Session, payload: PasteImportRequest) -> ListingRead:
    result = PasteImportAdapter().ingest(payload)
    if result.errors:
        raise HTTPException(status_code=422, detail=result.errors)
    logger.info("Paste import accepted source_url_present=%s", bool(payload.source_url))
    return _persist_ingestion_result(db, result, adapter_key="paste_import", run_mode="paste_import")[0]


def create_url_reference(db: Session, payload: UrlReferenceCreate) -> ListingRead:
    result = UrlReferenceAdapter().ingest(payload)
    logger.info("URL reference captured for %s", payload.url)
    return _persist_ingestion_result(db, result, adapter_key="url_reference", run_mode="url_reference")[0]


def create_clip_import(db: Session, payload: BrowserClipRequest) -> BrowserClipImportResponse:
    if _clip_payload_size(payload) > MAX_BROWSER_CLIP_TOTAL_CHARS:
        raise HTTPException(status_code=413, detail="Browser clip payload is too large. Select less page text or use the paste import.")

    criteria = ensure_default_criteria(db)
    result = BrowserClipAdapter().ingest(payload)
    if not result.listings:
        raise HTTPException(status_code=422, detail=result.errors or [{"message": "Could not create a listing from this browser clip."}])

    normalized = result.listings[0]
    source = _source_for_normalized(db, normalized)
    import_run = _create_import_run(db, source, "browser_clip", "browser_clip", result)
    warnings = list(result.warnings)
    duplicate_status = "created"

    exact_duplicate = _find_exact_source_duplicate(
        db,
        normalized.provenance.source_url,
        normalized.provenance.source_listing_id,
    )
    if exact_duplicate:
        duplicate_status = "updated_existing"
        warnings.append("Exact source URL matched an existing listing; updated that listing instead of creating a duplicate.")
        import_run.records_created = 0
        import_run.records_updated = 1
        import_run.warnings = warnings
        listing = _apply_normalized_update(db, exact_duplicate, normalized, import_run)
    else:
        possible_duplicates = _find_possible_duplicates(db, normalized)
        if possible_duplicates:
            duplicate_status = "possible_duplicate"
            duplicate_ids = [item.id for item in possible_duplicates]
            warnings.append(f"Possible duplicate detected by address, address/price, or title/city/price: listing IDs {duplicate_ids}.")
            normalized.provenance.raw_payload_json = {
                **normalized.provenance.raw_payload_json,
                "possible_duplicate_listing_ids": duplicate_ids,
            }
            normalized.feature_tags = list(dict.fromkeys(normalized.feature_tags + ["possible_duplicate"]))

        listing = _persist_normalized_listing(db, normalized, import_run)
        if possible_duplicates:
            listing.decision_status = "needs_review"
            listing.priority = "high"
            listing.next_action = "Review possible duplicate before contacting or touring."
            listing.raw_payload = {
                **(listing.raw_payload or {}),
                "possible_duplicate_listing_ids": [item.id for item in possible_duplicates],
            }
            import_run.warnings = warnings

    db.commit()
    sync_scores(db, criteria)
    logger.info("Browser clip imported source_domain=%s duplicate_status=%s", normalized.provenance.source_domain, duplicate_status)

    refreshed = db.scalar(
        select(Listing)
        .options(selectinload(Listing.source), selectinload(Listing.notes))
        .where(Listing.id == listing.id)
    )
    score = db.scalar(
        select(ListingScore).where(
            ListingScore.criteria_id == criteria.id,
            ListingScore.listing_id == listing.id,
        )
    )
    needs_review = refreshed.decision_status == "needs_review" or refreshed.listing_status == "needs_manual_review"
    if score and score.explanation:
        needs_review = needs_review or bool(score.explanation.get("needs_review_badges"))

    return BrowserClipImportResponse(
        data=BrowserClipImportData(
            listing_id=refreshed.id,
            source_name=refreshed.source.name,
            source_domain=refreshed.source_domain,
            source_url=refreshed.source_url or refreshed.listing_url or str(payload.source_url),
            fields_extracted=extracted_fields_for(normalized),
            needs_review=needs_review,
            duplicate_status=duplicate_status,
            warnings=warnings,
        )
    )


def create_csv_import(db: Session, payload: CsvImportRequest) -> CsvImportSummary:
    result = CsvImportAdapter().ingest(payload)
    logger.info("CSV import processed rows_received=%s rows_imported=%s rows_skipped=%s", result.rows_received, result.rows_imported, result.rows_skipped)
    listings = _persist_ingestion_result(db, result, adapter_key="csv_import", run_mode="csv_import") if result.listings else []
    return CsvImportSummary(
        rows_received=result.rows_received,
        rows_imported=result.rows_imported,
        rows_skipped=result.rows_skipped,
        errors=[ImportErrorRead(**error) for error in result.errors],
        warnings=result.warnings,
        listings=listings,
    )


def get_scores(db: Session) -> list[ScoreBreakdownRead]:
    criteria = ensure_default_criteria(db)
    scores = db.scalars(select(ListingScore).where(ListingScore.criteria_id == criteria.id)).all()
    scores.sort(key=lambda item: item.total_score, reverse=True)
    return [serialize_score(score) for score in scores if score is not None]


def get_score_breakdown(db: Session, listing_id: int) -> ScoreBreakdownRead:
    from fastapi import HTTPException

    criteria = ensure_default_criteria(db)
    score = db.scalar(
        select(ListingScore).where(
            ListingScore.criteria_id == criteria.id,
            ListingScore.listing_id == listing_id,
        )
    )
    if score is None:
        listing = db.scalar(select(Listing).where(Listing.id == listing_id))
        if listing is None:
            raise HTTPException(status_code=404, detail="Listing not found.")
        sync_scores(db, criteria)
        score = db.scalar(
            select(ListingScore).where(
                ListingScore.criteria_id == criteria.id,
                ListingScore.listing_id == listing_id,
            )
        )
    return serialize_score(score)


def update_listing_decision(db: Session, listing_id: int, payload: ListingDecisionUpdate) -> ListingRead:
    from fastapi import HTTPException

    listing = db.scalar(
        select(Listing)
        .options(selectinload(Listing.source), selectinload(Listing.notes))
        .where(Listing.id == listing_id)
    )
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(listing, field, value)
    db.add(listing)
    db.commit()
    sync_scores(db)
    criteria = ensure_default_criteria(db)
    score = db.scalar(select(ListingScore).where(ListingScore.criteria_id == criteria.id, ListingScore.listing_id == listing.id))
    db.refresh(listing)
    return serialize_listing(listing, score)


def update_listing_notes(db: Session, listing_id: int, payload: ListingNotesUpdate) -> ListingRead:
    from fastapi import HTTPException

    listing = db.scalar(select(Listing).where(Listing.id == listing_id))
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found.")
    db.add(ListingNote(listing_id=listing_id, author=payload.author, note=payload.note))
    if payload.author == "user":
        listing.private_notes = payload.note
    db.commit()
    sync_scores(db)
    criteria = ensure_default_criteria(db)
    refreshed = db.scalar(
        select(Listing)
        .options(selectinload(Listing.source), selectinload(Listing.notes))
        .where(Listing.id == listing_id)
    )
    score = db.scalar(select(ListingScore).where(ListingScore.criteria_id == criteria.id, ListingScore.listing_id == listing_id))
    return serialize_listing(refreshed, score)


def update_listing_watchlist(db: Session, listing_id: int, payload: ListingWatchlistUpdate) -> ListingRead:
    from fastapi import HTTPException

    listing = db.scalar(
        select(Listing)
        .options(selectinload(Listing.source), selectinload(Listing.notes))
        .where(Listing.id == listing_id)
    )
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found.")
    listing.watchlist_status = payload.watchlist_status
    if payload.priority:
        listing.priority = payload.priority
    db.add(
        WatchlistEntry(
            listing_id=listing.id,
            status=payload.watchlist_status,
            priority=payload.priority or listing.priority,
            reason=payload.reason,
        )
    )
    db.commit()
    sync_scores(db)
    criteria = ensure_default_criteria(db)
    score = db.scalar(select(ListingScore).where(ListingScore.criteria_id == criteria.id, ListingScore.listing_id == listing.id))
    db.refresh(listing)
    return serialize_listing(listing, score)
