from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.config import DEFAULT_SCORE_WEIGHTS


class SearchCriteriaBase(BaseModel):
    name: str = "Orange County Family Rental Search"
    county: str = "Orange County"
    state: str = "CA"
    city: str | None = None
    min_bedrooms: int = 3
    min_bathrooms: float = 2.0
    max_price: int | None = 6500
    min_sqft: int | None = 1400
    require_backyard: bool = True
    require_garage: bool = True
    pets_required: bool = False
    notes: str | None = None
    weights: dict[str, float] = Field(default_factory=lambda: DEFAULT_SCORE_WEIGHTS.copy())


class SearchCriteriaUpdate(SearchCriteriaBase):
    pass


class SearchCriteriaRead(SearchCriteriaBase):
    id: int
    is_active: bool
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ManualListingCreate(BaseModel):
    title: str
    address_line1: str | None = None
    city: str
    neighborhood: str | None = None
    county: str = "Orange County"
    state: str = "CA"
    postal_code: str | None = None
    price: float
    bedrooms: int
    bathrooms: float
    square_feet: int | None = None
    lot_size_sqft: int | None = None
    has_backyard: bool = False
    has_garage: bool = False
    garage_spaces: int | None = None
    pets_allowed: bool | None = None
    watchlist_status: str = "review"
    property_type: str = "single_family"
    listing_url: HttpUrl | None = None
    image_url: HttpUrl | None = None
    description: str | None = None
    note: str | None = None
    source_name: str = "Manual Import"


class ListingNoteRead(BaseModel):
    author: str
    note: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScoreBreakdownRead(BaseModel):
    listing_id: int
    criteria_id: int
    total_score: float
    price_score: float
    space_score: float
    location_score: float
    feature_score: float
    freshness_score: float
    confidence_score: float
    explanation: dict
    computed_at: datetime


class ListingRead(BaseModel):
    id: int
    title: str
    address_line1: str | None
    city: str
    neighborhood: str | None
    county: str
    state: str
    postal_code: str | None
    price: float
    bedrooms: int
    bathrooms: float
    square_feet: int | None
    has_backyard: bool
    has_garage: bool
    garage_spaces: int | None
    pets_allowed: bool | None
    watchlist_status: str
    property_type: str
    listing_url: str | None
    image_url: str | None
    description: str | None
    feature_tags: list[str]
    confidence: float
    listed_at: datetime | None
    last_seen_at: datetime | None
    source_name: str
    source_kind: str
    notes: list[ListingNoteRead] = Field(default_factory=list)
    score: ScoreBreakdownRead | None = None


class ListingFilterParams(BaseModel):
    county: str | None = None
    city: str | None = None
    min_bedrooms: int | None = None
    require_backyard: bool | None = None
    require_garage: bool | None = None
    pets_required: bool | None = None
    sort_by: str = "best_deal"

