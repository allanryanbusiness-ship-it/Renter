from fastapi.testclient import TestClient

from app.main import app


def test_url_reference_endpoint_marks_needs_manual_review() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/listings/url-reference",
            json={
                "url": "https://www.redfin.com/CA/Irvine/example-url-reference",
                "title": "Redfin URL Reference",
                "notes": "Review later",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_name"] == "Redfin"
    assert payload["source_type"] == "url_reference"
    assert payload["listing_status"] == "needs_manual_review"
    assert payload["decision_status"] == "needs_review"
