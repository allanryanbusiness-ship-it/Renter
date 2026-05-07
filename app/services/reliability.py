from __future__ import annotations

import csv
import json
import logging
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.config import APP_VERSION, BACKUP_DIR, DATABASE_PATH
from app.models import DiscoveryProvider, DiscoveryRun, Listing, ListingNote, ListingScore, SearchCriteria, Source, WatchlistEntry
from app.schemas import ListingFilterParams
from app.services.benchmark_service import load_benchmark_data, validate_benchmark_data
from app.services.listings import ensure_default_criteria, ensure_sources, get_listings, serialize_listing, sync_scores


logger = logging.getLogger(__name__)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_now() -> str:
    return utc_now().isoformat().replace("+00:00", "Z")


def latest_backup_path(backup_dir: Path = BACKUP_DIR) -> Path | None:
    if not backup_dir.exists():
        return None
    backups = sorted(backup_dir.glob("renter_*.sqlite"), key=lambda path: path.stat().st_mtime, reverse=True)
    return backups[0] if backups else None


def create_database_backup(source_path: Path = DATABASE_PATH, backup_dir: Path = BACKUP_DIR) -> dict[str, Any]:
    if not source_path.exists():
        raise HTTPException(status_code=404, detail=f"Database file not found: {source_path}")

    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = utc_now().strftime("%Y-%m-%d_%H%M%S")
    backup_path = backup_dir / f"renter_{timestamp}.sqlite"
    metadata_path = backup_dir / f"renter_{timestamp}.json"
    if backup_path.exists():
        raise HTTPException(status_code=409, detail=f"Backup path already exists: {backup_path}")

    with sqlite3.connect(source_path) as source_connection:
        with sqlite3.connect(backup_path) as backup_connection:
            source_connection.backup(backup_connection)

    metadata = {
        "created_at": iso_now(),
        "source_database_path": str(source_path),
        "backup_path": str(backup_path),
        "size_bytes": backup_path.stat().st_size,
        "app_version": APP_VERSION,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    logger.info("Database backup created at %s", backup_path)
    return metadata | {"metadata_path": str(metadata_path)}


def export_listings_payload(db: Session) -> dict[str, Any]:
    criteria = ensure_default_criteria(db)
    listings = get_listings(db, ListingFilterParams(sort_by="overall_score"))
    scores = [score.model_dump(mode="json") for score in [listing.score for listing in listings] if score]
    logger.info("JSON listings export generated")
    return {
        "meta": {
            "export_type": "listings",
            "generated_at": iso_now(),
            "app_version": APP_VERSION,
            "database_path": str(DATABASE_PATH),
        },
        "criteria": {
            "id": criteria.id,
            "name": criteria.name,
            "county": criteria.county,
            "state": criteria.state,
            "city": criteria.city,
            "preferred_cities": criteria.preferred_cities,
            "zip_codes": criteria.zip_codes,
            "min_bedrooms": criteria.min_bedrooms,
            "min_bathrooms": criteria.min_bathrooms,
            "max_price": criteria.max_price,
            "min_sqft": criteria.min_sqft,
            "require_backyard": criteria.require_backyard,
            "require_garage": criteria.require_garage,
            "allow_unknown_backyard": criteria.allow_unknown_backyard,
            "allow_unknown_garage": criteria.allow_unknown_garage,
            "pets_required": criteria.pets_required,
            "property_types": criteria.property_types,
            "provider_names": criteria.provider_names,
            "notes": criteria.notes,
            "weights": criteria.weights,
        },
        "listings": [listing.model_dump(mode="json") for listing in listings],
        "scores": scores,
    }


def export_full_payload(db: Session) -> dict[str, Any]:
    payload = export_listings_payload(db)
    payload["meta"]["export_type"] = "full"
    payload["sources"] = [
        {
            "name": source.name,
            "kind": source.kind,
            "adapter_key": source.adapter_key,
            "status": source.status,
            "base_url": source.base_url,
            "compliance_notes": source.compliance_notes,
            "enabled_by_default": source.enabled_by_default,
        }
        for source in db.scalars(select(Source).order_by(Source.name)).all()
    ]
    payload["discovery_providers"] = [
        {
            "id": provider.id,
            "key": provider.key,
            "source_name": provider.source_name,
            "source_type": provider.source_type,
            "status": provider.status,
            "enabled_by_default": provider.enabled_by_default,
            "configured": provider.configured,
            "requires_api_key": provider.requires_api_key,
            "docs_url": provider.docs_url,
            "compliance_notes": provider.compliance_notes,
            "last_seen_at": provider.last_seen_at.isoformat() if provider.last_seen_at else None,
        }
        for provider in db.scalars(select(DiscoveryProvider).order_by(DiscoveryProvider.key)).all()
    ]
    payload["discovery_runs"] = [
        {
            "id": run.id,
            "provider_key": run.provider_key,
            "source_name": run.source_name,
            "source_type": run.source_type,
            "status": run.status,
            "dry_run": run.dry_run,
            "import_results": run.import_results,
            "import_run_id": run.import_run_id,
            "criteria_snapshot": run.criteria_snapshot,
            "rows_received": run.rows_received,
            "rows_imported": run.rows_imported,
            "rows_skipped": run.rows_skipped,
            "records_created": run.records_created,
            "records_updated": run.records_updated,
            "possible_duplicates": run.possible_duplicates,
            "listing_ids": run.listing_ids,
            "candidate_preview": run.candidate_preview,
            "warnings": run.warnings,
            "errors": run.errors,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        }
        for run in db.scalars(select(DiscoveryRun).order_by(DiscoveryRun.id.desc()).limit(100)).all()
    ]
    payload["benchmarks"] = load_benchmark_data()
    logger.info("Full JSON export generated")
    return payload


def export_listings_csv(db: Session) -> str:
    listings = get_listings(db, ListingFilterParams(sort_by="overall_score"))
    output = StringIO()
    fieldnames = [
        "id",
        "title",
        "city",
        "price",
        "bedrooms",
        "bathrooms",
        "square_feet",
        "backyard_status",
        "garage_status",
        "source_name",
        "source_url",
        "decision_status",
        "watchlist_status",
        "overall_score",
        "deal_score",
        "market_label",
        "rent_delta_vs_median",
        "notes_count",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for listing in listings:
        score = listing.score
        writer.writerow(
            {
                "id": listing.id,
                "title": listing.title,
                "city": listing.city,
                "price": listing.price,
                "bedrooms": listing.bedrooms,
                "bathrooms": listing.bathrooms,
                "square_feet": listing.square_feet,
                "backyard_status": listing.backyard_status,
                "garage_status": listing.garage_status,
                "source_name": listing.source_name,
                "source_url": listing.source_url,
                "decision_status": listing.decision_status,
                "watchlist_status": listing.watchlist_status,
                "overall_score": score.overall_score if score else "",
                "deal_score": score.deal_score if score else "",
                "market_label": score.market_label if score else "",
                "rent_delta_vs_median": score.rent_delta_vs_median if score else "",
                "notes_count": len(listing.notes),
            }
        )
    logger.info("CSV listings export generated rows=%s", len(listings))
    return output.getvalue()


def _source_for_name(db: Session, source_name: str | None, source_kind: str | None = None) -> Source:
    ensure_sources(db)
    name = source_name or "Manual Import"
    source = db.scalar(select(Source).where(Source.name == name))
    if source is None:
        source = Source(
            name=name,
            kind=source_kind or "restored",
            adapter_key="full_json_import",
            status="active",
            enabled_by_default=True,
            compliance_notes="Created from safe full JSON restore/import.",
        )
        db.add(source)
        db.flush()
    return source


def _exact_duplicate_for_exported_listing(db: Session, item: dict[str, Any]) -> Listing | None:
    source_url = item.get("source_url") or item.get("listing_url")
    if source_url:
        duplicate = db.scalar(
            select(Listing)
            .options(selectinload(Listing.source), selectinload(Listing.notes))
            .where((Listing.source_url == source_url) | (Listing.listing_url == source_url))
            .limit(1)
        )
        if duplicate:
            return duplicate
    source_listing_id = item.get("source_listing_id")
    if source_listing_id:
        duplicate = db.scalar(
            select(Listing)
            .options(selectinload(Listing.source), selectinload(Listing.notes))
            .where((Listing.source_listing_id == source_listing_id) | (Listing.external_id == source_listing_id))
            .limit(1)
        )
        if duplicate:
            return duplicate
    return None


def _apply_exported_listing(listing: Listing, item: dict[str, Any], source: Source) -> None:
    listing.source_id = source.id
    listing.title = item.get("title") or listing.title
    listing.address_line1 = item.get("address_line1") or item.get("address") or listing.address_line1
    listing.city = item.get("city") or listing.city
    listing.neighborhood = item.get("neighborhood") or listing.neighborhood
    listing.county = item.get("county") or listing.county
    listing.state = item.get("state") or listing.state
    listing.postal_code = item.get("postal_code") or item.get("zip") or listing.postal_code
    listing.price = item.get("price") or item.get("price_monthly") or listing.price
    listing.bedrooms = item.get("bedrooms") or listing.bedrooms
    listing.bathrooms = item.get("bathrooms") or listing.bathrooms
    listing.square_feet = item.get("square_feet") or listing.square_feet
    listing.lot_size_sqft = item.get("lot_size_sqft") or item.get("lot_size") or listing.lot_size_sqft
    listing.has_backyard = bool(item.get("has_backyard", listing.has_backyard))
    listing.backyard_status = item.get("backyard_status") or listing.backyard_status
    listing.backyard_evidence = item.get("backyard_evidence") or listing.backyard_evidence
    listing.has_garage = bool(item.get("has_garage", listing.has_garage))
    listing.garage_status = item.get("garage_status") or listing.garage_status
    listing.garage_evidence = item.get("garage_evidence") or listing.garage_evidence
    listing.garage_spaces = item.get("garage_spaces") if item.get("garage_spaces") is not None else listing.garage_spaces
    listing.parking_details = item.get("parking_details") or listing.parking_details
    listing.pets_allowed = item.get("pets_allowed") if item.get("pets_allowed") is not None else listing.pets_allowed
    listing.pet_policy = item.get("pet_policy") or listing.pet_policy
    listing.laundry = item.get("laundry") or listing.laundry
    listing.air_conditioning = item.get("air_conditioning") or listing.air_conditioning
    listing.watchlist_status = item.get("watchlist_status") or listing.watchlist_status
    listing.property_type = item.get("property_type") or listing.property_type
    listing.listing_url = item.get("listing_url") or listing.listing_url
    listing.source_url = item.get("source_url") or listing.source_url or listing.listing_url
    listing.source_domain = item.get("source_domain") or listing.source_domain
    listing.source_listing_id = item.get("source_listing_id") or listing.source_listing_id
    listing.discovery_run_id = item.get("discovery_run_id") or listing.discovery_run_id
    listing.image_url = item.get("image_url") or listing.image_url
    listing.description = item.get("description") or listing.description
    listing.raw_text = item.get("raw_text") or listing.raw_text
    listing.raw_payload = item.get("raw_payload_json") or listing.raw_payload or {}
    listing.feature_tags = item.get("feature_tags") or listing.feature_tags or []
    listing.confidence = item.get("confidence") or listing.confidence
    listing.source_confidence = item.get("source_confidence") or listing.source_confidence
    listing.listing_status = item.get("listing_status") or listing.listing_status
    listing.decision_status = item.get("decision_status") or listing.decision_status
    listing.decision_reason = item.get("decision_reason") or listing.decision_reason
    listing.priority = item.get("priority") or listing.priority
    listing.next_action = item.get("next_action") or listing.next_action
    listing.contact_name = item.get("contact_name") or listing.contact_name
    listing.contact_phone = item.get("contact_phone") or listing.contact_phone
    listing.contact_email = item.get("contact_email") or listing.contact_email
    listing.user_rating = item.get("user_rating") if item.get("user_rating") is not None else listing.user_rating
    listing.private_notes = item.get("private_notes") or listing.private_notes
    listing.source_type = item.get("source_type") or listing.source_type
    listing.is_active = True


def import_full_json_merge(db: Session, payload: dict[str, Any]) -> dict[str, Any]:
    listings = payload.get("listings") or payload.get("data", {}).get("listings")
    if not isinstance(listings, list):
        raise HTTPException(status_code=422, detail="Expected exported JSON with a listings array.")

    summary = {
        "records_received": len(listings),
        "records_imported": 0,
        "records_updated": 0,
        "records_skipped": 0,
        "errors": [],
        "warnings": [],
    }
    for index, item in enumerate(listings, start=1):
        if not isinstance(item, dict):
            summary["records_skipped"] += 1
            summary["errors"].append({"row_number": index, "message": "Listing entry must be an object."})
            continue
        if not item.get("title") or not item.get("city") or not (item.get("price") or item.get("price_monthly")):
            summary["records_skipped"] += 1
            summary["errors"].append({"row_number": index, "message": "Listing is missing title, city, or price."})
            continue

        source = _source_for_name(db, item.get("source_name"), item.get("source_kind"))
        existing = _exact_duplicate_for_exported_listing(db, item)
        if existing:
            _apply_exported_listing(existing, item, source)
            listing = existing
            summary["records_updated"] += 1
        else:
            listing = Listing(
                source_id=source.id,
                title=item.get("title"),
                city=item.get("city"),
                county=item.get("county") or "Orange County",
                state=item.get("state") or "CA",
                price=item.get("price") or item.get("price_monthly"),
                bedrooms=item.get("bedrooms") or 0,
                bathrooms=item.get("bathrooms") or 0,
                feature_tags=[],
                raw_payload={},
            )
            _apply_exported_listing(listing, item, source)
            db.add(listing)
            db.flush()
            db.add(
                WatchlistEntry(
                    listing_id=listing.id,
                    status=listing.watchlist_status,
                    priority=listing.priority,
                    reason="Restored from full JSON import.",
                )
            )
            summary["records_imported"] += 1

        existing_notes = {note.note for note in listing.notes}
        for note in item.get("notes") or []:
            note_text = note.get("note") if isinstance(note, dict) else None
            if note_text and note_text not in existing_notes:
                db.add(ListingNote(listing_id=listing.id, author=note.get("author", "import"), note=note_text))
                existing_notes.add(note_text)

    db.commit()
    sync_scores(db)
    logger.info("Full JSON import completed: %s", summary)
    return summary


def data_quality_report(db: Session) -> dict[str, Any]:
    criteria = ensure_default_criteria(db)
    listings = db.scalars(
        select(Listing).options(selectinload(Listing.source), selectinload(Listing.notes)).where(Listing.is_active.is_(True))
    ).all()
    scores_by_listing = {
        score.listing_id
        for score in db.scalars(select(ListingScore).where(ListingScore.criteria_id == criteria.id)).all()
    }

    duplicate_buckets: dict[str, list[int]] = defaultdict(list)
    for listing in listings:
        if listing.source_url or listing.listing_url:
            duplicate_buckets[f"url:{listing.source_url or listing.listing_url}"].append(listing.id)
        if listing.address_line1:
            duplicate_buckets[f"address:{listing.address_line1.strip().lower()}"].append(listing.id)
        if listing.title and listing.city and float(listing.price) > 0:
            duplicate_buckets[f"title_city_price:{listing.title.lower()}|{listing.city.lower()}|{float(listing.price):.0f}"].append(listing.id)
    duplicates = {key: ids for key, ids in duplicate_buckets.items() if len(ids) > 1}

    benchmark_errors = validate_benchmark_data()
    benchmark_meta = load_benchmark_data().get("_meta", {})
    last_backup = latest_backup_path()
    counts = Counter(
        {
            "total_listings": len(listings),
            "missing_price": sum(float(listing.price) <= 0 for listing in listings),
            "missing_city": sum(not listing.city or listing.city == "Unknown" for listing in listings),
            "missing_source_url": sum(not (listing.source_url or listing.listing_url) for listing in listings),
            "unknown_backyard": sum(listing.backyard_status == "unknown" for listing in listings),
            "unknown_garage": sum(listing.garage_status == "unknown" for listing in listings),
            "missing_score_breakdown": sum(listing.id not in scores_by_listing for listing in listings),
            "needs_review": sum(listing.decision_status == "needs_review" or listing.watchlist_status == "needs_manual_review" for listing in listings),
            "potential_duplicate_groups": len(duplicates),
        }
    )

    warnings: list[str] = []
    if benchmark_errors:
        warnings.append("Benchmark file has validation errors.")
    if not last_backup:
        warnings.append("No database backup found yet.")
    if counts["missing_score_breakdown"]:
        warnings.append("Some listings are missing score breakdowns; refresh scoring or restart the app.")

    return {
        "data": {
            "database_path": str(DATABASE_PATH),
            "database_exists": DATABASE_PATH.exists(),
            "database_size_bytes": DATABASE_PATH.stat().st_size if DATABASE_PATH.exists() else 0,
            "backup_dir": str(BACKUP_DIR),
            "last_backup_path": str(last_backup) if last_backup else None,
            "last_backup_at": datetime.fromtimestamp(last_backup.stat().st_mtime, tz=timezone.utc).isoformat().replace("+00:00", "Z")
            if last_backup
            else None,
            "app_version": APP_VERSION,
            "counts": dict(counts),
            "duplicates": duplicates,
            "benchmark_last_reviewed": benchmark_meta.get("last_reviewed"),
            "benchmark_errors": benchmark_errors,
            "warnings": warnings,
        },
        "errors": [],
    }


def system_status(db: Session) -> dict[str, Any]:
    quality = data_quality_report(db)["data"]
    return {
        "data": {
            "app_version": APP_VERSION,
            "database_path": quality["database_path"],
            "database_exists": quality["database_exists"],
            "database_size_bytes": quality["database_size_bytes"],
            "backup_dir": quality["backup_dir"],
            "last_backup_path": quality["last_backup_path"],
            "last_backup_at": quality["last_backup_at"],
            "total_listings": quality["counts"]["total_listings"],
            "needs_review": quality["counts"]["needs_review"],
            "benchmark_last_reviewed": quality["benchmark_last_reviewed"],
            "warnings": quality["warnings"],
        },
        "errors": [],
    }
