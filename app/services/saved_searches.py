from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import DEFAULT_SEARCH_CRITERIA, ORANGE_COUNTY_DISCOVERY_CITIES
from app.models import SearchCriteria
from app.schemas import SavedSearchCreate, SavedSearchRead, SavedSearchUpdate


DEFAULT_SAVED_SEARCH_NAME = "Orange County 3BR Yard + Garage"


def ensure_default_saved_search(db: Session) -> SearchCriteria:
    existing = db.scalar(select(SearchCriteria).where(SearchCriteria.name == DEFAULT_SAVED_SEARCH_NAME).limit(1))
    if existing:
        changed = False
        if not existing.preferred_cities:
            existing.preferred_cities = ORANGE_COUNTY_DISCOVERY_CITIES
            changed = True
        if not existing.provider_names:
            existing.provider_names = ["mock"]
            changed = True
        if not existing.property_types:
            existing.property_types = ["single_family", "townhome"]
            changed = True
        if changed:
            existing.updated_at = datetime.utcnow()
            db.add(existing)
            db.commit()
            db.refresh(existing)
        return existing

    values = dict(DEFAULT_SEARCH_CRITERIA)
    values["name"] = DEFAULT_SAVED_SEARCH_NAME
    values["preferred_cities"] = list(ORANGE_COUNTY_DISCOVERY_CITIES)
    values["provider_names"] = ["mock"]
    values["property_types"] = ["single_family", "townhome"]
    saved_search = SearchCriteria(**values)
    db.add(saved_search)
    db.commit()
    db.refresh(saved_search)
    return saved_search


def list_saved_searches(db: Session) -> list[SavedSearchRead]:
    ensure_default_saved_search(db)
    rows = db.scalars(select(SearchCriteria).order_by(SearchCriteria.is_active.desc(), SearchCriteria.updated_at.desc())).all()
    return [_serialize_saved_search(row) for row in rows]


def create_saved_search(db: Session, payload: SavedSearchCreate) -> SavedSearchRead:
    row = SearchCriteria(**_payload_to_criteria_values(payload))
    db.add(row)
    db.commit()
    db.refresh(row)
    return _serialize_saved_search(row)


def update_saved_search(db: Session, saved_search_id: int, payload: SavedSearchUpdate) -> SavedSearchRead:
    row = db.get(SearchCriteria, saved_search_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Saved search not found.")

    values = payload.model_dump(exclude_unset=True)
    for field, value in values.items():
        if field == "cities":
            row.preferred_cities = value or []
        elif field == "backyard_required":
            row.require_backyard = bool(value)
        elif field == "garage_required":
            row.require_garage = bool(value)
        else:
            setattr(row, field, value)
    row.updated_at = datetime.utcnow()
    db.add(row)
    db.commit()
    db.refresh(row)
    return _serialize_saved_search(row)


def delete_saved_search(db: Session, saved_search_id: int) -> SavedSearchRead:
    row = db.get(SearchCriteria, saved_search_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Saved search not found.")
    row.is_active = False
    row.updated_at = datetime.utcnow()
    db.add(row)
    db.commit()
    db.refresh(row)
    return _serialize_saved_search(row)


def get_saved_search_or_404(db: Session, saved_search_id: int) -> SearchCriteria:
    ensure_default_saved_search(db)
    row = db.get(SearchCriteria, saved_search_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Saved search not found.")
    return row


def _payload_to_criteria_values(payload: SavedSearchCreate) -> dict:
    values = payload.model_dump()
    cities = values.pop("cities")
    values["preferred_cities"] = cities
    values["require_backyard"] = values.pop("backyard_required")
    values["require_garage"] = values.pop("garage_required")
    values["city"] = None
    values["weights"] = DEFAULT_SEARCH_CRITERIA["weights"]
    return values


def _serialize_saved_search(row: SearchCriteria) -> SavedSearchRead:
    cities = list(row.preferred_cities or [])
    return SavedSearchRead(
        id=row.id,
        name=row.name,
        county=row.county,
        state=row.state,
        cities=cities,
        preferred_cities=cities,
        zip_codes=list(row.zip_codes or []),
        min_bedrooms=row.min_bedrooms,
        min_bathrooms=row.min_bathrooms,
        max_price=row.max_price,
        min_sqft=row.min_sqft,
        backyard_required=row.require_backyard,
        garage_required=row.require_garage,
        require_backyard=row.require_backyard,
        require_garage=row.require_garage,
        allow_unknown_backyard=row.allow_unknown_backyard,
        allow_unknown_garage=row.allow_unknown_garage,
        pets_required=row.pets_required,
        property_types=list(row.property_types or []),
        provider_names=list(row.provider_names or []),
        notes=row.notes,
        is_active=row.is_active,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
