from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import ListingFilterParams, ListingRead, ManualListingCreate, ScoreBreakdownRead, SearchCriteriaRead, SearchCriteriaUpdate
from app.services.listings import create_manual_listing, get_active_criteria, get_listings, get_scores, update_search_criteria


router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/listings", response_model=list[ListingRead])
def listings(
    county: str | None = Query(default=None),
    city: str | None = Query(default=None),
    min_bedrooms: int | None = Query(default=None, ge=0),
    require_backyard: bool | None = Query(default=None),
    require_garage: bool | None = Query(default=None),
    pets_required: bool | None = Query(default=None),
    sort_by: str = Query(default="best_deal"),
    db: Session = Depends(get_db),
) -> list[ListingRead]:
    filters = ListingFilterParams(
        county=county,
        city=city,
        min_bedrooms=min_bedrooms,
        require_backyard=require_backyard,
        require_garage=require_garage,
        pets_required=pets_required,
        sort_by=sort_by,
    )
    return get_listings(db, filters)


@router.post("/listings/manual", response_model=ListingRead)
def add_manual_listing(payload: ManualListingCreate, db: Session = Depends(get_db)) -> ListingRead:
    return create_manual_listing(db, payload)


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

