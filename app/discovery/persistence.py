from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.discovery.adapters import DiscoveryProviderInfo
from app.models import DiscoveryProvider, DiscoveryRun


def sync_discovery_providers(db: Session, providers: list[DiscoveryProviderInfo]) -> dict[str, DiscoveryProvider]:
    synced: dict[str, DiscoveryProvider] = {}
    now = datetime.utcnow()
    for provider_info in providers:
        raw_values = asdict(provider_info)
        values = {
            key: value
            for key, value in raw_values.items()
            if key in DiscoveryProvider.__table__.columns
        }
        provider = db.scalar(select(DiscoveryProvider).where(DiscoveryProvider.key == provider_info.key))
        if provider is None:
            provider = DiscoveryProvider(**values)
            db.add(provider)
        else:
            for field, value in values.items():
                setattr(provider, field, value)
        provider.last_seen_at = now
        synced[provider_info.key] = provider
    db.commit()
    for provider in synced.values():
        db.refresh(provider)
    return synced


def create_discovery_run_record(
    db: Session,
    *,
    provider: DiscoveryProvider | None,
    provider_key: str,
    source_name: str,
    source_type: str,
    status: str,
    dry_run: bool,
    import_results: bool,
    criteria_snapshot: dict[str, Any],
    rows_received: int = 0,
    rows_imported: int = 0,
    rows_skipped: int = 0,
    records_created: int = 0,
    records_updated: int = 0,
    possible_duplicates: int = 0,
    listing_ids: list[int] | None = None,
    candidate_preview: list[dict[str, Any]] | None = None,
    warnings: list[str] | None = None,
    errors: list[dict[str, Any]] | None = None,
    import_run_id: int | None = None,
    started_at: datetime | None = None,
) -> DiscoveryRun:
    run = DiscoveryRun(
        provider_id=provider.id if provider else None,
        provider_key=provider_key,
        source_name=source_name,
        source_type=source_type,
        status=status,
        dry_run=dry_run,
        import_results=import_results,
        import_run_id=import_run_id,
        criteria_snapshot=criteria_snapshot,
        rows_received=rows_received,
        rows_imported=rows_imported,
        rows_skipped=rows_skipped,
        records_created=records_created,
        records_updated=records_updated,
        possible_duplicates=possible_duplicates,
        listing_ids=listing_ids or [],
        candidate_preview=candidate_preview or [],
        warnings=warnings or [],
        errors=errors or [],
        started_at=started_at or datetime.utcnow(),
        finished_at=datetime.utcnow(),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run
