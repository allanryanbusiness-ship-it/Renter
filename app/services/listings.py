from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.config import DEFAULT_SEARCH_CRITERIA
from app.models import ImportRun, Listing, ListingNote, ListingScore, SearchCriteria, Source, WatchlistEntry
from app.normalization.listings import normalize_manual_listing
from app.schemas import ListingFilterParams, ListingRead, ManualListingCreate, ScoreBreakdownRead, SearchCriteriaUpdate
from app.services.scoring import compute_listing_score


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
        "status": "planned",
        "base_url": None,
        "enabled_by_default": True,
        "compliance_notes": "Future adapter for user-controlled exports.",
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
]


def ensure_sources(db: Session) -> None:
    if db.scalar(select(Source.id).limit(1)):
        return

    for entry in SOURCE_CATALOG:
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
        db.add(
            ListingScore(
                listing_id=listing.id,
                criteria_id=criteria.id,
                **payload,
            )
        )

    db.commit()


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
        explanation=score.explanation,
        computed_at=score.computed_at,
    )


def serialize_listing(listing: Listing, score: ListingScore | None) -> ListingRead:
    return ListingRead(
        id=listing.id,
        title=listing.title,
        address_line1=listing.address_line1,
        city=listing.city,
        neighborhood=listing.neighborhood,
        county=listing.county,
        state=listing.state,
        postal_code=listing.postal_code,
        price=float(listing.price),
        bedrooms=listing.bedrooms,
        bathrooms=listing.bathrooms,
        square_feet=listing.square_feet,
        has_backyard=listing.has_backyard,
        has_garage=listing.has_garage,
        garage_spaces=listing.garage_spaces,
        pets_allowed=listing.pets_allowed,
        watchlist_status=listing.watchlist_status,
        property_type=listing.property_type,
        listing_url=listing.listing_url,
        image_url=listing.image_url,
        description=listing.description,
        feature_tags=listing.feature_tags,
        confidence=listing.confidence,
        listed_at=listing.listed_at,
        last_seen_at=listing.last_seen_at,
        source_name=listing.source.name,
        source_kind=listing.source.kind,
        notes=list(listing.notes),
        score=serialize_score(score),
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
    if filters.require_backyard:
        query = query.where(Listing.has_backyard.is_(True))
    if filters.require_garage:
        query = query.where(Listing.has_garage.is_(True))
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
    else:
        results.sort(key=lambda item: item.score.total_score if item.score else 0, reverse=True)

    return results


def create_manual_listing(db: Session, payload: ManualListingCreate) -> ListingRead:
    ensure_sources(db)
    criteria = ensure_default_criteria(db)

    source = db.scalar(select(Source).where(Source.name == payload.source_name))
    if source is None:
        source = Source(
            name=payload.source_name,
            kind="manual",
            adapter_key="manual",
            status="active",
            base_url=None,
            enabled_by_default=True,
            compliance_notes="Created from manual listing submission.",
        )
        db.add(source)
        db.flush()

    import_run = ImportRun(
        source_id=source.id,
        adapter_key="manual",
        run_mode="manual_entry",
        status="completed",
        records_seen=1,
        records_created=1,
        records_updated=0,
        started_at=datetime.utcnow(),
        finished_at=datetime.utcnow(),
    )
    db.add(import_run)
    db.flush()

    normalized = normalize_manual_listing(payload)
    listing = Listing(
        source_id=source.id,
        import_run_id=import_run.id,
        listed_at=datetime.utcnow(),
        last_seen_at=datetime.utcnow(),
        **normalized,
    )
    db.add(listing)
    db.flush()

    if payload.note:
        db.add(ListingNote(listing_id=listing.id, author="user", note=payload.note))

    db.add(
        WatchlistEntry(
            listing_id=listing.id,
            status=listing.watchlist_status,
            priority="high" if listing.watchlist_status in {"shortlist", "tour"} else "medium",
            reason="Created from manual dashboard submission.",
        )
    )
    db.commit()
    sync_scores(db, criteria)

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
    return serialize_listing(refreshed, score)


def get_scores(db: Session) -> list[ScoreBreakdownRead]:
    criteria = ensure_default_criteria(db)
    scores = db.scalars(select(ListingScore).where(ListingScore.criteria_id == criteria.id)).all()
    scores.sort(key=lambda item: item.total_score, reverse=True)
    return [serialize_score(score) for score in scores if score is not None]

