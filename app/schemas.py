from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from app.config import DEFAULT_SCORE_WEIGHTS


class SearchCriteriaBase(BaseModel):
    name: str = "Orange County 3BR Yard + Garage"
    county: str = "Orange County"
    state: str = "CA"
    city: str | None = None
    preferred_cities: list[str] = Field(default_factory=list)
    zip_codes: list[str] = Field(default_factory=list)
    min_bedrooms: int = 3
    min_bathrooms: float = 2.0
    max_price: int | None = 6500
    min_sqft: int | None = 1400
    require_backyard: bool = True
    require_garage: bool = True
    allow_unknown_backyard: bool = True
    allow_unknown_garage: bool = True
    pets_required: bool = False
    property_types: list[str] = Field(default_factory=list)
    provider_names: list[str] = Field(default_factory=list)
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
    backyard_status: str | None = None
    backyard_evidence: str | None = None
    has_garage: bool = False
    garage_status: str | None = None
    garage_evidence: str | None = None
    garage_spaces: int | None = None
    parking_details: str | None = None
    pets_allowed: bool | None = None
    pet_policy: str | None = None
    laundry: str | None = None
    air_conditioning: str | None = None
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
    hard_criteria_score: float = 0
    match_score: float = 0
    deal_score: float = 0
    data_completeness_score: float = 0
    completeness_score: float = 0
    source_reliability_score: float = 0
    overall_score: float = 0
    price_per_bedroom: float | None = None
    price_per_sqft: float | None = None
    benchmark_city: str | None = None
    benchmark_used: bool = False
    benchmark_used_fallback: bool = False
    benchmark_confidence: str | None = None
    benchmark_source_type: str | None = None
    median_rent_3br: float | None = None
    typical_low_3br: float | None = None
    typical_high_3br: float | None = None
    rent_delta_vs_median: float | None = None
    rent_delta_percent: float | None = None
    price_per_sqft_delta: float | None = None
    market_label: str | None = None
    benchmark_notes: str | None = None
    benchmark_sources: list[dict] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    needs_review_badges: list[str] = Field(default_factory=list)
    explanation: dict
    computed_at: datetime


class PasteImportRequest(BaseModel):
    raw_text: str = Field(min_length=1)
    source_name: str | None = None
    source_url: HttpUrl | None = None
    notes: str | None = None


class BrowserClipRequest(BaseModel):
    source_url: HttpUrl
    page_title: str | None = Field(default=None, max_length=500)
    selected_text: str | None = Field(default=None, max_length=20_000)
    page_text: str | None = Field(default=None, max_length=30_000)
    source_domain: str | None = Field(default=None, max_length=240)
    user_notes: str | None = Field(default=None, max_length=2_000)
    captured_at: datetime | None = None

    @field_validator("selected_text", "page_text", "page_title", "source_domain", "user_notes")
    @classmethod
    def blank_to_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class BrowserClipImportData(BaseModel):
    listing_id: int
    source_name: str
    source_domain: str | None = None
    source_url: str
    fields_extracted: list[str] = Field(default_factory=list)
    needs_review: bool
    duplicate_status: str = "created"
    warnings: list[str] = Field(default_factory=list)


class BrowserClipImportResponse(BaseModel):
    data: BrowserClipImportData
    meta: dict = Field(default_factory=lambda: {"import_type": "browser_clip"})
    errors: list[dict] = Field(default_factory=list)


class CsvImportRequest(BaseModel):
    csv_text: str = Field(min_length=1)
    source_name: str = "CSV Import"
    notes: str | None = None


class ImportErrorRead(BaseModel):
    row_number: int | None = None
    message: str


class CsvImportSummary(BaseModel):
    rows_received: int
    rows_imported: int
    rows_skipped: int
    errors: list[ImportErrorRead] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    listings: list["ListingRead"] = Field(default_factory=list)


class UrlReferenceCreate(BaseModel):
    url: HttpUrl
    title: str | None = None
    notes: str | None = None
    source_name: str | None = None


class DiscoveryProviderRead(BaseModel):
    id: int | None = None
    key: str
    source_name: str
    source_type: str
    provider_name: str | None = None
    provider_type: str | None = None
    status: str
    is_enabled: bool = False
    enabled_by_default: bool
    configured: bool
    requires_api_key: bool
    supported_locations: list[str] = Field(default_factory=list)
    supports_rentals: bool = True
    supports_filters: list[str] = Field(default_factory=list)
    docs_url: str | None = None
    rate_limit_notes: str | None = None
    compliance_notes: str
    last_seen_at: datetime | None = None


class ListingDiscoveryRunRequest(BaseModel):
    saved_search_id: int | None = Field(default=None, ge=1)
    provider_keys: list[str] = Field(default_factory=list)
    limit: int = Field(default=25, ge=1, le=100)
    dry_run: bool = False
    import_results: bool = True
    city: str | None = None
    preferred_cities: list[str] | None = None
    zip_codes: list[str] | None = None
    min_bedrooms: int | None = Field(default=None, ge=0)
    min_bathrooms: float | None = Field(default=None, ge=0)
    max_price: int | None = Field(default=None, ge=0)
    min_sqft: int | None = Field(default=None, ge=0)
    require_backyard: bool | None = None
    require_garage: bool | None = None
    allow_unknown_backyard: bool | None = None
    allow_unknown_garage: bool | None = None
    pets_required: bool | None = None
    property_types: list[str] | None = None
    provider_names: list[str] | None = None


class DiscoveryCandidatePreview(BaseModel):
    title: str
    city: str
    price: float
    bedrooms: int
    bathrooms: float
    source_name: str
    source_type: str
    source_url: str | None = None
    backyard_status: str
    garage_status: str
    confidence: float


class DiscoveryRunSummary(BaseModel):
    discovery_run_id: int | None = None
    provider_key: str
    source_name: str
    source_type: str | None = None
    status: str
    import_run_id: int | None = None
    rows_received: int = 0
    rows_imported: int = 0
    rows_skipped: int = 0
    records_created: int = 0
    records_updated: int = 0
    possible_duplicates: int = 0
    listing_ids: list[int] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[dict] = Field(default_factory=list)
    candidates: list[DiscoveryCandidatePreview] = Field(default_factory=list)


class DiscoveryRunRead(BaseModel):
    id: int
    provider_key: str
    source_name: str
    source_type: str
    status: str
    dry_run: bool
    import_results: bool
    import_run_id: int | None = None
    criteria_snapshot: dict = Field(default_factory=dict)
    rows_received: int
    rows_imported: int
    rows_skipped: int
    records_created: int
    records_updated: int
    possible_duplicates: int
    listing_ids: list[int] = Field(default_factory=list)
    candidate_preview: list[dict] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[dict] = Field(default_factory=list)
    started_at: datetime
    finished_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ListingDiscoveryRunResponse(BaseModel):
    data: dict
    errors: list[dict] = Field(default_factory=list)


class SavedSearchBase(BaseModel):
    name: str = "Orange County 3BR Yard + Garage"
    county: str = "Orange County"
    state: str = "CA"
    cities: list[str] = Field(default_factory=list)
    zip_codes: list[str] = Field(default_factory=list)
    min_bedrooms: int = Field(default=3, ge=0)
    min_bathrooms: float = Field(default=2.0, ge=0)
    max_price: int | None = Field(default=6500, ge=0)
    min_sqft: int | None = Field(default=1400, ge=0)
    backyard_required: bool = True
    garage_required: bool = True
    allow_unknown_backyard: bool = True
    allow_unknown_garage: bool = True
    pets_required: bool = False
    property_types: list[str] = Field(default_factory=list)
    provider_names: list[str] = Field(default_factory=list)
    notes: str | None = None
    is_active: bool = True


class SavedSearchCreate(SavedSearchBase):
    pass


class SavedSearchUpdate(BaseModel):
    name: str | None = None
    county: str | None = None
    state: str | None = None
    cities: list[str] | None = None
    zip_codes: list[str] | None = None
    min_bedrooms: int | None = Field(default=None, ge=0)
    min_bathrooms: float | None = Field(default=None, ge=0)
    max_price: int | None = Field(default=None, ge=0)
    min_sqft: int | None = Field(default=None, ge=0)
    backyard_required: bool | None = None
    garage_required: bool | None = None
    allow_unknown_backyard: bool | None = None
    allow_unknown_garage: bool | None = None
    pets_required: bool | None = None
    property_types: list[str] | None = None
    provider_names: list[str] | None = None
    notes: str | None = None
    is_active: bool | None = None


class SavedSearchRead(SavedSearchBase):
    id: int
    preferred_cities: list[str] = Field(default_factory=list)
    require_backyard: bool = True
    require_garage: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ListingDecisionUpdate(BaseModel):
    decision_status: str | None = None
    decision_reason: str | None = None
    priority: str | None = None
    next_action: str | None = None
    next_action_due_date: datetime | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    tour_date: datetime | None = None
    user_rating: int | None = Field(default=None, ge=1, le=5)
    private_notes: str | None = None


class ListingNotesUpdate(BaseModel):
    note: str
    author: str = "user"


class ListingWatchlistUpdate(BaseModel):
    watchlist_status: str
    priority: str | None = None
    reason: str | None = None


class ListingRead(BaseModel):
    id: int
    title: str
    address: str | None = None
    address_line1: str | None
    city: str
    neighborhood: str | None
    county: str
    state: str
    zip: str | None = None
    postal_code: str | None
    latitude: float | None = None
    longitude: float | None = None
    price_monthly: float
    price: float
    bedrooms: int
    bathrooms: float
    square_feet: int | None
    lot_size: int | None = None
    lot_size_sqft: int | None = None
    has_backyard: bool
    backyard_status: str
    backyard_evidence: str | None = None
    has_garage: bool
    garage_status: str
    garage_evidence: str | None = None
    garage_spaces: int | None
    parking_details: str | None = None
    pets_allowed: bool | None
    pet_policy: str | None = None
    laundry: str | None = None
    air_conditioning: str | None = None
    listing_status: str
    decision_status: str
    decision_reason: str | None = None
    priority: str
    next_action: str | None = None
    next_action_due_date: datetime | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    tour_date: datetime | None = None
    user_rating: int | None = None
    private_notes: str | None = None
    watchlist_status: str
    property_type: str
    source_url: str | None = None
    listing_url: str | None
    source_domain: str | None = None
    source_listing_id: str | None = None
    discovery_run_id: int | None = None
    image_url: str | None
    description: str | None
    raw_text: str | None = None
    raw_payload_json: dict = Field(default_factory=dict)
    feature_tags: list[str]
    confidence: float
    source_confidence: float
    match_score: float
    deal_score: float
    confidence_score: float
    first_seen_at: datetime | None = None
    listed_at: datetime | None
    last_seen_at: datetime | None
    imported_at: datetime | None = None
    updated_at: datetime | None = None
    source_name: str
    source_kind: str
    source_type: str
    notes: list[ListingNoteRead] = Field(default_factory=list)
    score: ScoreBreakdownRead | None = None
    score_breakdown: ScoreBreakdownRead | None = None


class ListingFilterParams(BaseModel):
    county: str | None = None
    city: str | None = None
    min_bedrooms: int | None = None
    backyard: str | None = None
    garage: str | None = None
    require_backyard: bool | None = None
    require_garage: bool | None = None
    pets_required: bool | None = None
    max_price: int | None = None
    source_name: str | None = None
    watchlist_status: str | None = None
    decision_status: str | None = None
    needs_review: bool | None = None
    discovery_only: bool | None = None
    new_from_discovery: bool | None = None
    needs_review_from_discovery: bool | None = None
    sort_by: str = "best_deal"


CsvImportSummary.model_rebuild()
