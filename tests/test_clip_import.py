from uuid import uuid4
from urllib.parse import urlparse

from fastapi.testclient import TestClient

from app.main import app


def _clip_payload(source_url: str, *, title: str | None = None, selected_text: str | None = None) -> dict:
    suffix = uuid4().hex[:8]
    address_number = int(suffix[:4], 16) % 9000 + 100
    source_domain = (urlparse(source_url).hostname or "").removeprefix("www.")
    return {
        "source_url": source_url,
        "page_title": title or f"Irvine clip fixture {suffix}",
        "selected_text": selected_text
        or (
            f"{address_number} Test Arbor Dr, Irvine, CA 92620. $4,650 per month. "
            f"3 bedrooms 2.5 baths 1,850 sqft. Private backyard. Attached two-car garage. "
            f"Washer dryer and central air. Fixture {suffix}."
        ),
        "source_domain": source_domain,
        "user_notes": "Captured by test bookmarklet fallback.",
        "captured_at": "2026-05-06T12:00:00Z",
    }


def _listing_by_id(client: TestClient, listing_id: int) -> dict:
    listings = client.get("/api/listings").json()
    return next(item for item in listings if item["id"] == listing_id)


def test_clip_import_endpoint_creates_listing_with_summary() -> None:
    url = f"https://www.zillow.com/homedetails/clip-create-{uuid4().hex}"
    with TestClient(app) as client:
        response = client.post("/api/import/clip", json=_clip_payload(url))

    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["import_type"] == "browser_clip"
    assert payload["data"]["listing_id"] > 0
    assert payload["data"]["source_name"] == "Zillow"
    assert payload["data"]["source_domain"] == "zillow.com"
    assert payload["data"]["source_url"] == url
    assert payload["data"]["duplicate_status"] == "created"
    assert {"price_monthly", "bedrooms", "bathrooms", "garage_status", "backyard_status"}.issubset(
        set(payload["data"]["fields_extracted"])
    )


def test_clip_import_sanitizes_text_before_storage() -> None:
    url = f"https://www.redfin.com/CA/Irvine/clip-sanitize-{uuid4().hex}"
    with TestClient(app) as client:
        response = client.post(
            "/api/import/clip",
            json=_clip_payload(
                url,
                title="<b>Redfin clipped listing</b>",
                selected_text=(
                    "<script>alert(1)</script> 44 Test Lane, Irvine, CA 92620. "
                    "$4,700 monthly 3 bedrooms 2 baths 1,700 sqft backyard garage"
                ),
            ),
        )
        listing = _listing_by_id(client, response.json()["data"]["listing_id"])

    assert response.status_code == 200
    assert "<script" not in listing["raw_text"].lower()
    assert "alert(1)" not in listing["raw_text"].lower()
    assert listing["title"] == "Redfin clipped listing"


def test_clip_import_rejects_large_payload() -> None:
    url = f"https://www.zillow.com/homedetails/clip-large-{uuid4().hex}"
    with TestClient(app) as client:
        response = client.post(
            "/api/import/clip",
            json={
                "source_url": url,
                "page_title": "Large clip",
                "selected_text": "x" * 20_000,
                "page_text": "y" * 30_000,
                "source_domain": "zillow.com",
                "user_notes": "z" * 1_000,
                "captured_at": "2026-05-06T12:00:00Z",
            },
        )

    assert response.status_code == 413


def test_fallback_json_payload_import_uses_same_endpoint() -> None:
    url = f"https://www.apartments.com/clip-fallback-{uuid4().hex}"
    fallback_json = _clip_payload(
        url,
        title="Fallback Apartments clip",
        selected_text=(
            "99 Fallback Way, Tustin, CA 92782. $4,250 per month. "
            "3 beds 2 baths 1,600 sqft fenced yard attached garage pets considered."
        ),
    )

    with TestClient(app) as client:
        response = client.post("/api/import/clip", json=fallback_json)

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["listing_id"] > 0
    assert data["source_name"] == "Apartments.com"
    assert data["duplicate_status"] in {"created", "possible_duplicate"}
