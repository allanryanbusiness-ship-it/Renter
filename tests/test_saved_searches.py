from fastapi.testclient import TestClient

from app.main import app


def test_default_saved_search_exists_with_orange_county_discovery_defaults() -> None:
    with TestClient(app) as client:
        response = client.get("/api/saved-searches")

    assert response.status_code == 200
    searches = response.json()
    default = next(item for item in searches if item["name"] == "Orange County 3BR Yard + Garage")
    assert default["county"] == "Orange County"
    assert default["state"] == "CA"
    assert default["min_bedrooms"] == 3
    assert default["backyard_required"] is True
    assert default["garage_required"] is True
    assert default["allow_unknown_backyard"] is True
    assert default["allow_unknown_garage"] is True
    assert "Irvine" in default["cities"]
    assert "Yorba Linda" in default["cities"]
    assert default["provider_names"] == ["mock"]


def test_saved_search_crud_and_discovery_run_selection() -> None:
    with TestClient(app) as client:
        create_response = client.post(
            "/api/saved-searches",
            json={
                "name": "Test Costa Mesa Discovery",
                "county": "Orange County",
                "state": "CA",
                "cities": ["Costa Mesa"],
                "zip_codes": ["92627"],
                "min_bedrooms": 3,
                "min_bathrooms": 2,
                "max_price": 6000,
                "min_sqft": 1200,
                "backyard_required": True,
                "garage_required": True,
                "allow_unknown_backyard": True,
                "allow_unknown_garage": True,
                "property_types": ["single_family"],
                "provider_names": ["mock"],
                "notes": "Integration test saved search.",
            },
        )

        assert create_response.status_code == 200
        saved_search = create_response.json()
        assert saved_search["cities"] == ["Costa Mesa"]
        assert saved_search["zip_codes"] == ["92627"]

        update_response = client.put(
            f"/api/saved-searches/{saved_search['id']}",
            json={"max_price": 5500, "cities": ["Costa Mesa", "Tustin"]},
        )
        assert update_response.status_code == 200
        assert update_response.json()["max_price"] == 5500
        assert update_response.json()["cities"] == ["Costa Mesa", "Tustin"]

        run_response = client.post(
            "/api/discovery/run",
            json={
                "saved_search_id": saved_search["id"],
                "provider_keys": ["mock"],
                "limit": 5,
                "dry_run": True,
                "import_results": False,
            },
        )
        assert run_response.status_code == 200
        summary = run_response.json()["data"]["summaries"][0]
        assert summary["provider_key"] == "mock"
        assert summary["status"] == "dry_run"

        delete_response = client.delete(f"/api/saved-searches/{saved_search['id']}")
        assert delete_response.status_code == 200
        assert delete_response.json()["is_active"] is False
