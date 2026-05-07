import json
import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import BACKUP_DIR, DATABASE_PATH, resolve_database_path
from app.main import app
from app.services.reliability import create_database_backup


def test_database_path_uses_configured_stable_location() -> None:
    assert resolve_database_path() == DATABASE_PATH
    assert DATABASE_PATH.name == "renter-test.db"
    assert str(DATABASE_PATH).startswith("/tmp/renter-dashboard-tests")


def test_backup_creation_writes_timestamped_sqlite_and_metadata(tmp_path: Path) -> None:
    source = tmp_path / "source.sqlite"
    backup_dir = tmp_path / "backups"
    with sqlite3.connect(source) as connection:
        connection.execute("CREATE TABLE demo (id INTEGER PRIMARY KEY, name TEXT)")
        connection.execute("INSERT INTO demo (name) VALUES ('ok')")

    backup = create_database_backup(source_path=source, backup_dir=backup_dir)

    backup_path = Path(backup["backup_path"])
    metadata_path = Path(backup["metadata_path"])
    assert backup_path.exists()
    assert metadata_path.exists()
    assert backup_path.name.startswith("renter_")
    assert json.loads(metadata_path.read_text())["source_database_path"] == str(source)


def test_backup_endpoint_creates_backup_for_app_database() -> None:
    with TestClient(app) as client:
        response = client.post("/api/admin/backup")

    assert response.status_code == 200
    payload = response.json()
    assert Path(payload["data"]["backup_path"]).exists()
    assert Path(payload["data"]["backup_path"]).parent == BACKUP_DIR


def test_json_csv_and_full_exports_include_scores_and_provenance() -> None:
    with TestClient(app) as client:
        listings_json = client.get("/api/export/listings.json")
        listings_csv = client.get("/api/export/listings.csv")
        full_json = client.get("/api/export/full.json")

    assert listings_json.status_code == 200
    listings_payload = listings_json.json()
    assert listings_payload["listings"]
    assert listings_payload["listings"][0]["score"]["benchmark_city"]
    assert listings_payload["listings"][0]["source_url"]

    assert listings_csv.status_code == 200
    assert "text/csv" in listings_csv.headers["content-type"]
    assert "market_label" in listings_csv.text.splitlines()[0]

    assert full_json.status_code == 200
    full_payload = full_json.json()
    assert full_payload["sources"]
    assert full_payload["benchmarks"]
    assert "discovery_providers" in full_payload
    assert "discovery_runs" in full_payload


def test_full_json_import_merge_updates_without_destructive_reset() -> None:
    with TestClient(app) as client:
        exported = client.get("/api/export/full.json").json()
        original_count = len(client.get("/api/listings").json())
        exported["listings"][0]["decision_status"] = "contacted"
        imported = client.post("/api/import/full-json", json=exported)
        after = client.get("/api/listings").json()

    assert imported.status_code == 200
    summary = imported.json()["data"]
    assert summary["records_received"] == original_count
    assert summary["records_updated"] >= 1
    assert len(after) == original_count
    assert any(listing["decision_status"] == "contacted" for listing in after)


def test_data_quality_and_status_endpoints_report_local_state() -> None:
    with TestClient(app) as client:
        quality = client.get("/api/admin/data-quality")
        status = client.get("/api/admin/status")

    assert quality.status_code == 200
    quality_data = quality.json()["data"]
    assert quality_data["database_exists"] is True
    assert quality_data["counts"]["total_listings"] >= 1
    assert "missing_source_url" in quality_data["counts"]

    assert status.status_code == 200
    status_data = status.json()["data"]
    assert status_data["database_path"] == str(DATABASE_PATH)
    assert status_data["total_listings"] >= 1
