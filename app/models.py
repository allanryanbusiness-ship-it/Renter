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


class SearchCriteria(TimestampMixin, Base):
    __tablename__ = "search_criteria"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    county: Mapped[str] = mapped_column(String(120), nullable=False)
    state: Mapped[str] = mapped_column(String(10), nullable=False, default="CA")
    city: Mapped[str | None] = mapped_column(String(120))
    min_bedrooms: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    min_bathrooms: Mapped[float] = mapped_column(Float, default=2.0, nullable=False)
    max_price: Mapped[int | None] = mapped_column(Integer)
    min_sqft: Mapped[int | None] = mapped_column(Integer)
    require_backyard: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    require_garage: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    pets_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    weights: Mapped[dict[str, float]] = mapped_column(JSON, default=dict, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    scores: Mapped[list["ListingScore"]] = relationship(back_populates="criteria")


class Listing(TimestampMixin, Base):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), nullable=False)
    import_run_id: Mapped[int | None] = mapped_column(ForeignKey("import_runs.id"))
    external_id: Mapped[str | None] = mapped_column(String(120))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    address_line1: Mapped[str | None] = mapped_column(String(200))
    city: Mapped[str] = mapped_column(String(120), nullable=False)
    neighborhood: Mapped[str | None] = mapped_column(String(120))
    county: Mapped[str] = mapped_column(String(120), nullable=False)
    state: Mapped[str] = mapped_column(String(10), default="CA", nullable=False)
    postal_code: Mapped[str | None] = mapped_column(String(20))
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    bedrooms: Mapped[int] = mapped_column(Integer, nullable=False)
    bathrooms: Mapped[float] = mapped_column(Float, nullable=False)
    square_feet: Mapped[int | None] = mapped_column(Integer)
    lot_size_sqft: Mapped[int | None] = mapped_column(Integer)
    has_backyard: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_garage: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    garage_spaces: Mapped[int | None] = mapped_column(Integer)
    pets_allowed: Mapped[bool | None] = mapped_column(Boolean)
    watchlist_status: Mapped[str] = mapped_column(String(40), default="review", nullable=False)
    property_type: Mapped[str] = mapped_column(String(80), default="single_family", nullable=False)
    listing_url: Mapped[str | None] = mapped_column(String(500))
    image_url: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    feature_tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.75, nullable=False)
    listed_at: Mapped[datetime | None] = mapped_column(DateTime)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    source: Mapped["Source"] = relationship(back_populates="listings")
    import_run: Mapped[ImportRun | None] = relationship(back_populates="listings")
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
