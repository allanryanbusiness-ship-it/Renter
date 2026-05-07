from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.discovery.adapters import (
    ListingDiscoveryCriteria,
    ProviderConfigurationError,
    discovery_adapter_registry,
    list_discovery_provider_info,
)
from app.discovery.persistence import create_discovery_run_record, sync_discovery_providers
from app.models import DiscoveryRun, Listing, SearchCriteria
from app.schemas import (
    DiscoveryCandidatePreview,
    DiscoveryProviderRead,
    DiscoveryRunRead,
    DiscoveryRunSummary,
    ListingDiscoveryRunRequest,
    ListingDiscoveryRunResponse,
)
from app.services.listings import ensure_default_criteria, persist_discovery_result
from app.services.saved_searches import get_saved_search_or_404


def get_discovery_providers(db: Session) -> list[DiscoveryProviderRead]:
    provider_infos = list_discovery_provider_info()
    provider_info_by_key = {provider.key: provider for provider in provider_infos}
    provider_rows = sync_discovery_providers(db, provider_infos)
    return [
        DiscoveryProviderRead(
            id=provider.id,
            key=provider.key,
            source_name=provider.source_name,
            source_type=provider.source_type,
            provider_name=provider_info_by_key[provider.key].provider_name,
            provider_type=provider_info_by_key[provider.key].provider_type,
            status=provider.status,
            is_enabled=provider_info_by_key[provider.key].is_enabled,
            enabled_by_default=provider.enabled_by_default,
            configured=provider.configured,
            requires_api_key=provider.requires_api_key,
            supported_locations=provider_info_by_key[provider.key].supported_locations,
            supports_rentals=provider_info_by_key[provider.key].supports_rentals,
            supports_filters=provider_info_by_key[provider.key].supports_filters,
            docs_url=provider.docs_url,
            rate_limit_notes=provider_info_by_key[provider.key].rate_limit_notes,
            compliance_notes=provider.compliance_notes or "",
            last_seen_at=provider.last_seen_at,
        )
        for provider in sorted(provider_rows.values(), key=lambda row: row.key)
    ]


def get_discovery_runs(db: Session, limit: int = 20) -> list[DiscoveryRunRead]:
    rows = db.scalars(select(DiscoveryRun).order_by(DiscoveryRun.id.desc()).limit(limit)).all()
    return [DiscoveryRunRead.model_validate(row) for row in rows]


def get_discovery_provider_run(db: Session, run_id: int) -> DiscoveryRunRead:
    row = db.get(DiscoveryRun, run_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Discovery run not found.")
    return DiscoveryRunRead.model_validate(row)


def run_listing_discovery(db: Session, payload: ListingDiscoveryRunRequest) -> ListingDiscoveryRunResponse:
    base_criteria = get_saved_search_or_404(db, payload.saved_search_id) if payload.saved_search_id else ensure_default_criteria(db)
    criteria = _criteria_from_payload(base_criteria, payload)
    criteria_snapshot = _criteria_snapshot(criteria)
    registry = discovery_adapter_registry()
    provider_rows = sync_discovery_providers(db, list_discovery_provider_info())
    provider_keys = payload.provider_keys or payload.provider_names or criteria.provider_names or [
        key for key, adapter in registry.items() if adapter.enabled_by_default and adapter.configured
    ]
    if not provider_keys:
        provider_keys = ["approved_demo_feed"]

    unknown = [key for key in provider_keys if key not in registry]
    if unknown:
        raise HTTPException(status_code=422, detail=[{"message": f"Unknown discovery provider: {key}"} for key in unknown])

    summaries: list[DiscoveryRunSummary] = []
    imported_listings = []
    response_errors: list[dict] = []

    for provider_key in provider_keys:
        adapter = registry[provider_key]
        provider_row = provider_rows.get(provider_key)
        run_started_at = datetime.utcnow()
        try:
            result = adapter.discover(criteria)
        except ProviderConfigurationError as exc:
            error = {"provider_key": provider_key, "message": str(exc)}
            response_errors.append(error)
            run = create_discovery_run_record(
                db,
                provider=provider_row,
                provider_key=provider_key,
                source_name=adapter.source_name,
                source_type=adapter.source_type,
                status="skipped",
                dry_run=payload.dry_run,
                import_results=payload.import_results,
                criteria_snapshot=criteria_snapshot,
                errors=[error],
                started_at=run_started_at,
            )
            summaries.append(
                DiscoveryRunSummary(
                    discovery_run_id=run.id,
                    provider_key=provider_key,
                    source_name=adapter.source_name,
                    source_type=adapter.source_type,
                    status="skipped",
                    errors=[error],
                )
            )
            continue

        if payload.dry_run or not payload.import_results:
            candidates = [_candidate_preview(item) for item in result.listings]
            run = create_discovery_run_record(
                db,
                provider=provider_row,
                provider_key=provider_key,
                source_name=adapter.source_name,
                source_type=adapter.source_type,
                status="dry_run",
                dry_run=True,
                import_results=False,
                criteria_snapshot=criteria_snapshot,
                rows_received=result.rows_received,
                rows_imported=result.rows_imported,
                rows_skipped=result.rows_skipped,
                candidate_preview=[candidate.model_dump(mode="json") for candidate in candidates],
                warnings=result.warnings,
                errors=result.errors,
                started_at=run_started_at,
            )
            summaries.append(
                DiscoveryRunSummary(
                    discovery_run_id=run.id,
                    provider_key=provider_key,
                    source_name=adapter.source_name,
                    source_type=adapter.source_type,
                    status="dry_run",
                    rows_received=result.rows_received,
                    rows_imported=result.rows_imported,
                    rows_skipped=result.rows_skipped,
                    warnings=result.warnings,
                    errors=result.errors,
                    candidates=candidates,
                )
            )
            continue

        persisted = persist_discovery_result(db, result, adapter_key=provider_key)
        imported_listings.extend(persisted["listings"])
        status = "completed_with_errors" if persisted["errors"] else "completed"
        run = create_discovery_run_record(
            db,
            provider=provider_row,
            provider_key=provider_key,
            source_name=adapter.source_name,
            source_type=adapter.source_type,
            status=status,
            dry_run=False,
            import_results=True,
            import_run_id=persisted["import_run_id"],
            criteria_snapshot=criteria_snapshot,
            rows_received=persisted["rows_received"],
            rows_imported=persisted["rows_imported"],
            rows_skipped=persisted["rows_skipped"],
            records_created=persisted["records_created"],
            records_updated=persisted["records_updated"],
            possible_duplicates=persisted["possible_duplicates"],
            listing_ids=persisted["listing_ids"],
            warnings=persisted["warnings"],
            errors=persisted["errors"],
            started_at=run_started_at,
        )
        _link_discovery_run_to_listings(db, run.id, persisted["listing_ids"])
        for listing in imported_listings:
            if listing.id in persisted["listing_ids"]:
                listing.discovery_run_id = run.id
                listing.raw_payload_json = {
                    **(listing.raw_payload_json or {}),
                    "discovery_run_id": run.id,
                }
        summaries.append(
            DiscoveryRunSummary(
                discovery_run_id=run.id,
                provider_key=provider_key,
                source_name=adapter.source_name,
                source_type=adapter.source_type,
                status=status,
                import_run_id=persisted["import_run_id"],
                rows_received=persisted["rows_received"],
                rows_imported=persisted["rows_imported"],
                rows_skipped=persisted["rows_skipped"],
                records_created=persisted["records_created"],
                records_updated=persisted["records_updated"],
                possible_duplicates=persisted["possible_duplicates"],
                listing_ids=persisted["listing_ids"],
                warnings=persisted["warnings"],
                errors=persisted["errors"],
            )
        )

    return ListingDiscoveryRunResponse(
        data={
            "criteria": criteria_snapshot,
            "providers": provider_keys,
            "summaries": [summary.model_dump(mode="json") for summary in summaries],
            "listings": [listing.model_dump(mode="json") for listing in imported_listings],
        },
        errors=response_errors,
    )


def _criteria_snapshot(criteria: ListingDiscoveryCriteria) -> dict:
    return {
        "county": criteria.county,
        "state": criteria.state,
        "city": criteria.city,
        "preferred_cities": criteria.preferred_cities or [],
        "zip_codes": criteria.zip_codes or [],
        "min_bedrooms": criteria.min_bedrooms,
        "min_bathrooms": criteria.min_bathrooms,
        "max_price": criteria.max_price,
        "min_sqft": criteria.min_sqft,
        "require_backyard": criteria.require_backyard,
        "require_garage": criteria.require_garage,
        "allow_unknown_backyard": criteria.allow_unknown_backyard,
        "allow_unknown_garage": criteria.allow_unknown_garage,
        "pets_required": criteria.pets_required,
        "property_types": criteria.property_types or [],
        "provider_names": criteria.provider_names or [],
        "limit": criteria.limit,
    }


def _criteria_from_payload(criteria: SearchCriteria, payload: ListingDiscoveryRunRequest) -> ListingDiscoveryCriteria:
    return ListingDiscoveryCriteria(
        county=criteria.county,
        state=criteria.state,
        city=payload.city if payload.city is not None else criteria.city,
        preferred_cities=payload.preferred_cities if payload.preferred_cities is not None else list(criteria.preferred_cities or []),
        zip_codes=payload.zip_codes if payload.zip_codes is not None else list(criteria.zip_codes or []),
        min_bedrooms=payload.min_bedrooms if payload.min_bedrooms is not None else criteria.min_bedrooms,
        min_bathrooms=payload.min_bathrooms if payload.min_bathrooms is not None else criteria.min_bathrooms,
        max_price=payload.max_price if payload.max_price is not None else criteria.max_price,
        min_sqft=payload.min_sqft if payload.min_sqft is not None else criteria.min_sqft,
        require_backyard=payload.require_backyard if payload.require_backyard is not None else criteria.require_backyard,
        require_garage=payload.require_garage if payload.require_garage is not None else criteria.require_garage,
        allow_unknown_backyard=(
            payload.allow_unknown_backyard if payload.allow_unknown_backyard is not None else criteria.allow_unknown_backyard
        ),
        allow_unknown_garage=payload.allow_unknown_garage if payload.allow_unknown_garage is not None else criteria.allow_unknown_garage,
        pets_required=payload.pets_required if payload.pets_required is not None else criteria.pets_required,
        property_types=payload.property_types if payload.property_types is not None else list(criteria.property_types or []),
        provider_names=payload.provider_names if payload.provider_names is not None else list(criteria.provider_names or []),
        limit=payload.limit,
    )


def _candidate_preview(listing) -> DiscoveryCandidatePreview:
    return DiscoveryCandidatePreview(
        title=listing.title,
        city=listing.city,
        price=listing.price_monthly,
        bedrooms=listing.bedrooms,
        bathrooms=listing.bathrooms,
        source_name=listing.provenance.source_name,
        source_type=listing.provenance.source_type,
        source_url=listing.provenance.source_url,
        backyard_status=listing.backyard_status,
        garage_status=listing.garage_status,
        confidence=listing.provenance.source_confidence,
    )


def _link_discovery_run_to_listings(db: Session, discovery_run_id: int, listing_ids: list[int]) -> None:
    if not listing_ids:
        return
    listings = db.scalars(select(Listing).where(Listing.id.in_(listing_ids))).all()
    for listing in listings:
        listing.discovery_run_id = discovery_run_id
        listing.raw_payload = {
            **(listing.raw_payload or {}),
            "discovery_run_id": discovery_run_id,
        }
        db.add(listing)
    db.commit()
