from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db import SessionLocal
from app.main import app
from app.models import DiscoveryProvider, DiscoveryRun, Listing
from app.services.listings import persist_discovery_result
from app.sources.base import IngestionResult, NormalizedListing, Provenance
from app.sources.discovery import ApprovedProviderFeedAdapter, ListingDiscoveryCriteria, MockDiscoveryProviderAdapter


def test_discovery_providers_endpoint_lists_safe_and_configured_states() -> None:
    with TestClient(app) as client:
        response = client.get("/api/discovery/providers")

    assert response.status_code == 200
    providers = {item["key"]: item for item in response.json()}
    assert providers["approved_demo_feed"]["configured"] is True
    assert providers["approved_demo_feed"]["enabled_by_default"] is True
    assert providers["approved_demo_feed"]["source_type"] == "provider_feed"
    assert providers["mock"]["configured"] is True
    assert providers["mock"]["source_type"] == "mock_provider"
    assert providers["mock"]["supports_rentals"] is True
    assert "city" in providers["mock"]["supports_filters"]
    assert providers["approved_json_api"]["configured"] is False
    assert providers["approved_json_api"]["status"] == "not_configured"
    assert providers["apify"]["status"] == "not_implemented"
    assert providers["brightdata"]["status"] == "not_implemented"
    assert providers["approved_demo_feed"]["id"] is not None

    with SessionLocal() as db:
        provider_rows = db.scalars(select(DiscoveryProvider)).all()

    assert {provider.key for provider in provider_rows} >= {"approved_demo_feed", "mock", "approved_json_api", "apify", "brightdata"}


def test_mock_provider_implements_required_adapter_surface() -> None:
    adapter = MockDiscoveryProviderAdapter()

    assert adapter.provider_name == "Mock Discovery Provider"
    assert adapter.provider_type == "mock_provider"
    assert adapter.is_enabled is True
    assert adapter.requires_api_key is False
    assert adapter.validate_config() is True
    result = adapter.search(ListingDiscoveryCriteria(limit=1))
    assert result.listings
    assert adapter.normalize({"title": "Incomplete", "price": 5000}) is None


def test_approved_provider_feed_filters_by_search_criteria() -> None:
    result = ApprovedProviderFeedAdapter().discover(ListingDiscoveryCriteria(limit=10))

    assert result.rows_received == 5
    assert result.rows_imported == 4
    assert result.rows_skipped == 1
    assert all(listing.bedrooms >= 3 for listing in result.listings)
    assert all(listing.backyard_status != "no" for listing in result.listings)
    assert all(listing.garage_status != "no" for listing in result.listings)
    assert any(listing.listing_status == "needs_manual_review" for listing in result.listings)


def test_automatic_discovery_imports_scores_and_provenance() -> None:
    with TestClient(app) as client:
        response = client.post("/api/discovery/run", json={"provider_keys": ["approved_demo_feed"], "limit": 3})

    assert response.status_code == 200
    payload = response.json()
    summary = payload["data"]["summaries"][0]
    assert summary["provider_key"] == "approved_demo_feed"
    assert summary["discovery_run_id"] is not None
    assert summary["rows_imported"] == 3
    assert summary["records_created"] + summary["records_updated"] >= 1
    assert payload["data"]["listings"]
    listing = payload["data"]["listings"][0]
    assert listing["source_name"] == "Approved Demo Provider Feed"
    assert listing["source_type"] == "provider_feed"
    assert listing["discovery_run_id"] == summary["discovery_run_id"]
    assert listing["raw_payload_json"]["discovery_run_id"] == summary["discovery_run_id"]
    assert listing["score"]["overall_score"] > 0
    assert "automatic_discovery" in listing["feature_tags"]

    with SessionLocal() as db:
        run = db.get(DiscoveryRun, summary["discovery_run_id"])

    assert run is not None
    assert run.provider_key == "approved_demo_feed"
    assert run.import_run_id == summary["import_run_id"]
    assert run.records_created == summary["records_created"]
    assert run.criteria_snapshot["min_bedrooms"] == 3

    with TestClient(app) as client:
        runs_response = client.get("/api/discovery/runs?limit=1")
        run_response = client.get(f"/api/discovery/runs/{summary['discovery_run_id']}")
        discovery_listings_response = client.get("/api/listings?discovery_only=true")

    assert runs_response.status_code == 200
    assert runs_response.json()[0]["id"] == summary["discovery_run_id"]
    assert run_response.status_code == 200
    assert run_response.json()["criteria_snapshot"]["min_bedrooms"] == 3
    assert discovery_listings_response.status_code == 200
    assert any(item["discovery_run_id"] == summary["discovery_run_id"] for item in discovery_listings_response.json())

    with SessionLocal() as db:
        linked_listing = db.get(Listing, summary["listing_ids"][0])
        assert linked_listing.discovery_run_id == summary["discovery_run_id"]
        assert linked_listing.raw_payload["discovery_run_id"] == summary["discovery_run_id"]


def test_discovery_deduplicates_exact_source_urls_on_repeated_runs() -> None:
    with TestClient(app) as client:
        first = client.post("/api/discovery/run", json={"provider_keys": ["approved_demo_feed"], "limit": 1})
        listing_count_after_first = len(client.get("/api/listings").json())
        second = client.post("/api/discovery/run", json={"provider_keys": ["approved_demo_feed"], "limit": 1})
        listing_count_after_second = len(client.get("/api/listings").json())

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["data"]["summaries"][0]["records_updated"] >= 1
    assert listing_count_after_second == listing_count_after_first


def test_discovery_deduplicates_by_source_listing_id_and_preserves_user_state() -> None:
    first_seen = datetime(2026, 5, 1, 8, 0, 0)
    second_seen = datetime(2026, 5, 7, 8, 0, 0)

    first_result = IngestionResult(
        listings=[
            _normalized_discovery_listing(
                source_url="https://example.com/provider/original-source-id-test",
                source_listing_id="source-id-dedupe-test-001",
                imported_at=first_seen,
            )
        ],
        rows_received=1,
        rows_imported=1,
    )
    second_result = IngestionResult(
        listings=[
            _normalized_discovery_listing(
                source_url="https://example.com/provider/changed-source-id-test",
                source_listing_id="source-id-dedupe-test-001",
                imported_at=second_seen,
                price=4595,
            )
        ],
        rows_received=1,
        rows_imported=1,
    )

    with SessionLocal() as db:
        first = persist_discovery_result(db, first_result, adapter_key="mock")
        listing_id = first["listing_ids"][0]
        listing = db.get(Listing, listing_id)
        listing.decision_status = "contacted"
        listing.watchlist_status = "shortlist"
        listing.private_notes = "Preserve this user note."
        db.commit()

        second = persist_discovery_result(db, second_result, adapter_key="mock")
        refreshed = db.get(Listing, listing_id)
        duplicates = db.scalars(
            select(Listing).where(Listing.source_listing_id == "source-id-dedupe-test-001", Listing.is_active.is_(True))
        ).all()

    assert second["records_updated"] == 1
    assert second["records_created"] == 0
    assert second["listing_ids"] == [listing_id]
    assert len(duplicates) == 1
    assert refreshed.decision_status == "contacted"
    assert refreshed.watchlist_status == "shortlist"
    assert refreshed.private_notes == "Preserve this user note."
    assert refreshed.first_seen_at == first_seen
    assert refreshed.last_seen_at > refreshed.first_seen_at


def test_discovery_dry_run_returns_candidates_without_importing() -> None:
    with TestClient(app) as client:
        before = len(client.get("/api/listings").json())
        response = client.post(
            "/api/discovery/run",
            json={"provider_keys": ["approved_demo_feed"], "limit": 2, "dry_run": True, "import_results": False},
        )
        after = len(client.get("/api/listings").json())

    assert response.status_code == 200
    summary = response.json()["data"]["summaries"][0]
    assert summary["status"] == "dry_run"
    assert summary["discovery_run_id"] is not None
    assert summary["candidates"]
    assert after == before

    with SessionLocal() as db:
        run = db.get(DiscoveryRun, summary["discovery_run_id"])

    assert run is not None
    assert run.dry_run is True
    assert run.import_results is False
    assert run.candidate_preview


def test_unconfigured_approved_json_api_provider_is_skipped_without_network_call() -> None:
    with TestClient(app) as client:
        response = client.post("/api/discovery/run", json={"provider_keys": ["approved_json_api"], "limit": 1})

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["summaries"][0]["status"] == "skipped"
    assert payload["data"]["summaries"][0]["discovery_run_id"] is not None
    assert payload["errors"]
    assert "RENTAL_DASHBOARD_PROVIDER_API_URL" in payload["errors"][0]["message"]


def test_mock_discovery_endpoint_imports_without_credentials() -> None:
    with TestClient(app) as client:
        response = client.post("/api/discovery/run", json={"provider_keys": ["mock"], "limit": 2})

    assert response.status_code == 200
    summary = response.json()["data"]["summaries"][0]
    assert summary["provider_key"] == "mock"
    assert summary["discovery_run_id"] is not None
    assert summary["rows_imported"] == 2
    assert summary["records_created"] + summary["records_updated"] >= 1


def test_provider_description_extracts_backyard_and_garage_evidence() -> None:
    listing = MockDiscoveryProviderAdapter().normalize(
        {
            "id": "description-extraction-test",
            "title": "Irvine rental with clues",
            "sourceUrl": "https://example.com/mock/description-extraction-test",
            "city": "Irvine",
            "county": "Orange County",
            "state": "CA",
            "price": 4500,
            "bedrooms": 3,
            "bathrooms": 2.5,
            "propertyType": "Single Family",
            "description": "Private yard, attached garage, central AC, and washer dryer hookups.",
        },
        ListingDiscoveryCriteria(limit=1),
    )

    assert listing is not None
    assert listing.backyard_status == "yes"
    assert "yard" in listing.backyard_evidence.lower()
    assert listing.garage_status == "yes"
    assert "garage" in listing.garage_evidence.lower()


def _normalized_discovery_listing(
    *,
    source_url: str,
    source_listing_id: str,
    imported_at: datetime,
    price: float = 4495,
) -> NormalizedListing:
    return NormalizedListing(
        title="Source ID Deduplication Test Home",
        address="100 Source Id Lane",
        city="Irvine",
        county="Orange County",
        state="CA",
        zip="92620",
        price_monthly=price,
        bedrooms=3,
        bathrooms=2.5,
        square_feet=1700,
        property_type="single_family",
        backyard_status="yes",
        backyard_evidence="Private fenced backyard.",
        garage_status="yes",
        garage_evidence="Attached two-car garage.",
        listing_status="active",
        watchlist_status="review",
        feature_tags=["automatic_discovery"],
        provenance=Provenance(
            source_name="Mock Discovery Provider",
            source_type="mock_provider",
            source_url=source_url,
            source_domain="example.com",
            source_listing_id=source_listing_id,
            source_confidence=0.86,
            imported_at=imported_at,
            raw_text="Private fenced backyard. Attached two-car garage.",
            raw_payload_json={"source_record": {"id": source_listing_id}},
        ),
    )
