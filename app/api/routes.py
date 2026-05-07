from fastapi import APIRouter, Body, Depends, Query
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import (
    BrowserClipImportResponse,
    BrowserClipRequest,
    CsvImportRequest,
    CsvImportSummary,
    DiscoveryProviderRead,
    DiscoveryRunRead,
    ListingDecisionUpdate,
    ListingDiscoveryRunRequest,
    ListingDiscoveryRunResponse,
    ListingFilterParams,
    ListingRead,
    ListingNotesUpdate,
    ListingWatchlistUpdate,
    ManualListingCreate,
    PasteImportRequest,
    SavedSearchCreate,
    SavedSearchRead,
    SavedSearchUpdate,
    ScoreBreakdownRead,
    SearchCriteriaRead,
    SearchCriteriaUpdate,
    UrlReferenceCreate,
)
from app.services.discovery import get_discovery_provider_run, get_discovery_providers, get_discovery_runs, run_listing_discovery
from app.services.listings import (
    create_clip_import,
    create_csv_import,
    create_manual_listing,
    create_paste_import,
    create_url_reference,
    get_active_criteria,
    get_listings,
    get_score_breakdown,
    get_scores,
    update_listing_decision,
    update_listing_notes,
    update_listing_watchlist,
    update_search_criteria,
)
from app.services.reliability import (
    create_database_backup,
    data_quality_report,
    export_full_payload,
    export_listings_csv,
    export_listings_payload,
    import_full_json_merge,
    system_status,
)
from app.services.saved_searches import create_saved_search, delete_saved_search, list_saved_searches, update_saved_search


router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/listings", response_model=list[ListingRead])
def listings(
    county: str | None = Query(default=None),
    city: str | None = Query(default=None),
    min_bedrooms: int | None = Query(default=None, ge=0),
    max_price: int | None = Query(default=None, ge=0),
    backyard: str | None = Query(default=None),
    garage: str | None = Query(default=None),
    require_backyard: bool | None = Query(default=None),
    require_garage: bool | None = Query(default=None),
    pets_required: bool | None = Query(default=None),
    source_name: str | None = Query(default=None),
    watchlist_status: str | None = Query(default=None),
    decision_status: str | None = Query(default=None),
    needs_review: bool | None = Query(default=None),
    discovery_only: bool | None = Query(default=None),
    new_from_discovery: bool | None = Query(default=None),
    needs_review_from_discovery: bool | None = Query(default=None),
    sort_by: str = Query(default="best_deal"),
    db: Session = Depends(get_db),
) -> list[ListingRead]:
    filters = ListingFilterParams(
        county=county,
        city=city,
        min_bedrooms=min_bedrooms,
        max_price=max_price,
        backyard=backyard,
        garage=garage,
        require_backyard=require_backyard,
        require_garage=require_garage,
        pets_required=pets_required,
        source_name=source_name,
        watchlist_status=watchlist_status,
        decision_status=decision_status,
        needs_review=needs_review,
        discovery_only=discovery_only,
        new_from_discovery=new_from_discovery,
        needs_review_from_discovery=needs_review_from_discovery,
        sort_by=sort_by,
    )
    return get_listings(db, filters)


@router.post("/listings/manual", response_model=ListingRead)
def add_manual_listing(payload: ManualListingCreate, db: Session = Depends(get_db)) -> ListingRead:
    return create_manual_listing(db, payload)


@router.post("/import/paste", response_model=ListingRead)
def import_pasted_listing(payload: PasteImportRequest, db: Session = Depends(get_db)) -> ListingRead:
    return create_paste_import(db, payload)


@router.post("/import/clip", response_model=BrowserClipImportResponse)
def import_browser_clip(payload: BrowserClipRequest, db: Session = Depends(get_db)) -> BrowserClipImportResponse:
    return create_clip_import(db, payload)


@router.post("/import/csv", response_model=CsvImportSummary)
def import_csv(payload: CsvImportRequest, db: Session = Depends(get_db)) -> CsvImportSummary:
    return create_csv_import(db, payload)


@router.post("/listings/url-reference", response_model=ListingRead)
def add_url_reference(payload: UrlReferenceCreate, db: Session = Depends(get_db)) -> ListingRead:
    return create_url_reference(db, payload)


@router.get("/discovery/providers", response_model=list[DiscoveryProviderRead])
def discovery_providers(db: Session = Depends(get_db)) -> list[DiscoveryProviderRead]:
    return get_discovery_providers(db)


@router.post("/discovery/run", response_model=ListingDiscoveryRunResponse)
def run_discovery(payload: ListingDiscoveryRunRequest, db: Session = Depends(get_db)) -> ListingDiscoveryRunResponse:
    return run_listing_discovery(db, payload)


@router.get("/discovery/runs", response_model=list[DiscoveryRunRead])
def discovery_runs(limit: int = Query(default=20, ge=1, le=100), db: Session = Depends(get_db)) -> list[DiscoveryRunRead]:
    return get_discovery_runs(db, limit=limit)


@router.get("/discovery/runs/{run_id}", response_model=DiscoveryRunRead)
def discovery_run_detail(run_id: int, db: Session = Depends(get_db)) -> DiscoveryRunRead:
    return get_discovery_provider_run(db, run_id)


@router.get("/saved-searches", response_model=list[SavedSearchRead])
def saved_searches(db: Session = Depends(get_db)) -> list[SavedSearchRead]:
    return list_saved_searches(db)


@router.post("/saved-searches", response_model=SavedSearchRead)
def post_saved_search(payload: SavedSearchCreate, db: Session = Depends(get_db)) -> SavedSearchRead:
    return create_saved_search(db, payload)


@router.put("/saved-searches/{saved_search_id}", response_model=SavedSearchRead)
def put_saved_search(saved_search_id: int, payload: SavedSearchUpdate, db: Session = Depends(get_db)) -> SavedSearchRead:
    return update_saved_search(db, saved_search_id, payload)


@router.delete("/saved-searches/{saved_search_id}", response_model=SavedSearchRead)
def remove_saved_search(saved_search_id: int, db: Session = Depends(get_db)) -> SavedSearchRead:
    return delete_saved_search(db, saved_search_id)


@router.get("/listings/{listing_id}/score-breakdown", response_model=ScoreBreakdownRead)
def listing_score_breakdown(listing_id: int, db: Session = Depends(get_db)) -> ScoreBreakdownRead:
    return get_score_breakdown(db, listing_id)


@router.patch("/listings/{listing_id}/decision", response_model=ListingRead)
def patch_listing_decision(
    listing_id: int,
    payload: ListingDecisionUpdate,
    db: Session = Depends(get_db),
) -> ListingRead:
    return update_listing_decision(db, listing_id, payload)


@router.patch("/listings/{listing_id}/notes", response_model=ListingRead)
def patch_listing_notes(
    listing_id: int,
    payload: ListingNotesUpdate,
    db: Session = Depends(get_db),
) -> ListingRead:
    return update_listing_notes(db, listing_id, payload)


@router.patch("/listings/{listing_id}/watchlist", response_model=ListingRead)
def patch_listing_watchlist(
    listing_id: int,
    payload: ListingWatchlistUpdate,
    db: Session = Depends(get_db),
) -> ListingRead:
    return update_listing_watchlist(db, listing_id, payload)


@router.get("/search-criteria", response_model=SearchCriteriaRead)
def read_search_criteria(db: Session = Depends(get_db)) -> SearchCriteriaRead:
    return get_active_criteria(db)


@router.post("/search-criteria", response_model=SearchCriteriaRead)
def save_search_criteria(
    payload: SearchCriteriaUpdate,
    db: Session = Depends(get_db),
) -> SearchCriteriaRead:
    return update_search_criteria(db, payload)


@router.get("/scores", response_model=list[ScoreBreakdownRead])
def scores(db: Session = Depends(get_db)) -> list[ScoreBreakdownRead]:
    return get_scores(db)


@router.get("/admin/status")
def admin_status(db: Session = Depends(get_db)) -> dict:
    return system_status(db)


@router.post("/admin/backup")
def backup_database() -> dict:
    return {"data": create_database_backup(), "errors": []}


@router.get("/admin/data-quality")
def data_quality(db: Session = Depends(get_db)) -> dict:
    return data_quality_report(db)


@router.get("/export/listings.json")
def export_listings_json(db: Session = Depends(get_db)) -> JSONResponse:
    return JSONResponse(export_listings_payload(db))


@router.get("/export/full.json")
def export_full_json(db: Session = Depends(get_db)) -> JSONResponse:
    return JSONResponse(export_full_payload(db))


@router.get("/export/listings.csv")
def export_listings_csv_endpoint(db: Session = Depends(get_db)) -> Response:
    csv_text = export_listings_csv(db)
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=renter_listings.csv"},
    )


@router.post("/import/full-json")
def import_full_json(payload: dict = Body(...), db: Session = Depends(get_db)) -> dict:
    return {"data": import_full_json_merge(db, payload), "errors": []}
