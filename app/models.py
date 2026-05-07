from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class Source(TimestampMixin, Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    kind: Mapped[str] = mapped_column(String(50), nullable=False, default="manual")
    adapter_key: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="active")
    base_url: Mapped[str | None] = mapped_column(String(400))
    compliance_notes: Mapped[str | None] = mapped_column(Text)
    enabled_by_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    listings: Mapped[list["Listing"]] = relationship(back_populates="source")
    import_runs: Mapped[list["ImportRun"]] = relationship(back_populates="source")


class ImportRun(TimestampMixin, Base):
    __tablename__ = "import_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), nullable=False)
    adapter_key: Mapped[str] = mapped_column(String(100), nullable=False)
    run_mode: Mapped[str] = mapped_column(String(40), nullable=False, default="seed")
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="completed")
    records_seen: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_updated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    warnings: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    error_text: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)

    source: Mapped["Source"] = relationship(back_populates="import_runs")
    listings: Mapped[list["Listing"]] = relationship(back_populates="import_run")


class DiscoveryProvider(TimestampMixin, Base):
    __tablename__ = "discovery_providers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    source_name: Mapped[str] = mapped_column(String(160), nullable=False)
    source_type: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(80), nullable=False)
    enabled_by_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    configured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_api_key: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    docs_url: Mapped[str | None] = mapped_column(String(500))
    compliance_notes: Mapped[str | None] = mapped_column(Text)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    discovery_runs: Mapped[list["DiscoveryRun"]] = relationship(back_populates="provider")


class DiscoveryRun(TimestampMixin, Base):
    __tablename__ = "discovery_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider_id: Mapped[int | None] = mapped_column(ForeignKey("discovery_providers.id"))
    provider_key: Mapped[str] = mapped_column(String(100), nullable=False)
    source_name: Mapped[str] = mapped_column(String(160), nullable=False)
    source_type: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(80), nullable=False)
    dry_run: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    import_results: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    import_run_id: Mapped[int | None] = mapped_column(ForeignKey("import_runs.id"))
    criteria_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    rows_received: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rows_imported: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rows_skipped: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_updated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    possible_duplicates: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    listing_ids: Mapped[list[int]] = mapped_column(JSON, default=list, nullable=False)
    candidate_preview: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    warnings: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    errors: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)

    provider: Mapped[DiscoveryProvider | None] = relationship(back_populates="discovery_runs")
    import_run: Mapped[ImportRun | None] = relationship()


class SearchCriteria(TimestampMixin, Base):
    __tablename__ = "search_criteria"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    county: Mapped[str] = mapped_column(String(120), nullable=False)
    state: Mapped[str] = mapped_column(String(10), nullable=False, default="CA")
    city: Mapped[str | None] = mapped_column(String(120))
    preferred_cities: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    zip_codes: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    min_bedrooms: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    min_bathrooms: Mapped[float] = mapped_column(Float, default=2.0, nullable=False)
    max_price: Mapped[int | None] = mapped_column(Integer)
    min_sqft: Mapped[int | None] = mapped_column(Integer)
    require_backyard: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    require_garage: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    allow_unknown_backyard: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    allow_unknown_garage: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    pets_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    property_types: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    provider_names: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    weights: Mapped[dict[str, float]] = mapped_column(JSON, default=dict, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    scores: Mapped[list["ListingScore"]] = relationship(back_populates="criteria")


class Listing(TimestampMixin, Base):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), nullable=False)
    import_run_id: Mapped[int | None] = mapped_column(ForeignKey("import_runs.id"))
    discovery_run_id: Mapped[int | None] = mapped_column(ForeignKey("discovery_runs.id"))
    external_id: Mapped[str | None] = mapped_column(String(120))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    address_line1: Mapped[str | None] = mapped_column(String(200))
    city: Mapped[str] = mapped_column(String(120), nullable=False)
    neighborhood: Mapped[str | None] = mapped_column(String(120))
    county: Mapped[str] = mapped_column(String(120), nullable=False)
    state: Mapped[str] = mapped_column(String(10), default="CA", nullable=False)
    postal_code: Mapped[str | None] = mapped_column(String(20))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    bedrooms: Mapped[int] = mapped_column(Integer, nullable=False)
    bathrooms: Mapped[float] = mapped_column(Float, nullable=False)
    square_feet: Mapped[int | None] = mapped_column(Integer)
    lot_size_sqft: Mapped[int | None] = mapped_column(Integer)
    has_backyard: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    backyard_status: Mapped[str] = mapped_column(String(20), default="unknown", nullable=False)
    backyard_evidence: Mapped[str | None] = mapped_column(Text)
    has_garage: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    garage_status: Mapped[str] = mapped_column(String(20), default="unknown", nullable=False)
    garage_evidence: Mapped[str | None] = mapped_column(Text)
    garage_spaces: Mapped[int | None] = mapped_column(Integer)
    parking_details: Mapped[str | None] = mapped_column(Text)
    pets_allowed: Mapped[bool | None] = mapped_column(Boolean)
    pet_policy: Mapped[str | None] = mapped_column(Text)
    laundry: Mapped[str | None] = mapped_column(String(120))
    air_conditioning: Mapped[str | None] = mapped_column(String(120))
    watchlist_status: Mapped[str] = mapped_column(String(40), default="review", nullable=False)
    property_type: Mapped[str] = mapped_column(String(80), default="single_family", nullable=False)
    listing_url: Mapped[str | None] = mapped_column(String(500))
    source_url: Mapped[str | None] = mapped_column(String(500))
    source_domain: Mapped[str | None] = mapped_column(String(240))
    source_type: Mapped[str] = mapped_column(String(80), default="manual", nullable=False)
    source_listing_id: Mapped[str | None] = mapped_column(String(120))
    image_url: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    raw_text: Mapped[str | None] = mapped_column(Text)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    feature_tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.75, nullable=False)
    source_confidence: Mapped[float] = mapped_column(Float, default=0.75, nullable=False)
    match_score: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    deal_score: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    first_seen_at: Mapped[datetime | None] = mapped_column(DateTime)
    listed_at: Mapped[datetime | None] = mapped_column(DateTime)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime)
    imported_at: Mapped[datetime | None] = mapped_column(DateTime)
    listing_status: Mapped[str] = mapped_column(String(40), default="active", nullable=False)
    decision_status: Mapped[str] = mapped_column(String(40), default="new", nullable=False)
    decision_reason: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(40), default="medium", nullable=False)
    next_action: Mapped[str | None] = mapped_column(Text)
    next_action_due_date: Mapped[datetime | None] = mapped_column(DateTime)
    contact_name: Mapped[str | None] = mapped_column(String(160))
    contact_phone: Mapped[str | None] = mapped_column(String(80))
    contact_email: Mapped[str | None] = mapped_column(String(160))
    tour_date: Mapped[datetime | None] = mapped_column(DateTime)
    user_rating: Mapped[int | None] = mapped_column(Integer)
    private_notes: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    source: Mapped["Source"] = relationship(back_populates="listings")
    import_run: Mapped[ImportRun | None] = relationship(back_populates="listings")
    discovery_run: Mapped[DiscoveryRun | None] = relationship()
    scores: Mapped[list["ListingScore"]] = relationship(back_populates="listing")
    notes: Mapped[list["ListingNote"]] = relationship(back_populates="listing")
    watchlist_entries: Mapped[list["WatchlistEntry"]] = relationship(back_populates="listing")


class ListingScore(Base):
    __tablename__ = "listing_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"), nullable=False)
    criteria_id: Mapped[int] = mapped_column(ForeignKey("search_criteria.id"), nullable=False)
    total_score: Mapped[float] = mapped_column(Float, nullable=False)
    price_score: Mapped[float] = mapped_column(Float, nullable=False)
    space_score: Mapped[float] = mapped_column(Float, nullable=False)
    location_score: Mapped[float] = mapped_column(Float, nullable=False)
    feature_score: Mapped[float] = mapped_column(Float, nullable=False)
    freshness_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    hard_criteria_score: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    deal_score: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    data_completeness_score: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    source_reliability_score: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    explanation: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    listing: Mapped["Listing"] = relationship(back_populates="scores")
    criteria: Mapped["SearchCriteria"] = relationship(back_populates="scores")


class ListingNote(Base):
    __tablename__ = "listing_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"), nullable=False)
    note: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(String(80), default="user", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    listing: Mapped["Listing"] = relationship(back_populates="notes")


class WatchlistEntry(Base):
    __tablename__ = "watchlist_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="review", nullable=False)
    priority: Mapped[str] = mapped_column(String(40), default="medium", nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    listing: Mapped["Listing"] = relationship(back_populates="watchlist_entries")
