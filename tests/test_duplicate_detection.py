from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def _payload(url: str, title: str, text: str, notes: str = "Clip note") -> dict:
    return {
        "source_url": url,
        "page_title": title,
        "selected_text": text,
        "source_domain": "redfin.com",
        "user_notes": notes,
        "captured_at": "2026-05-06T12:00:00Z",
    }


def _listing_by_id(client: TestClient, listing_id: int) -> dict:
    listings = client.get("/api/listings").json()
    return next(item for item in listings if item["id"] == listing_id)


def test_exact_source_url_duplicate_updates_existing_and_preserves_decision_and_notes() -> None:
    unique = uuid4().hex
    url = f"https://www.redfin.com/CA/Irvine/exact-duplicate-{unique}"
    first_text = (
        "1 Exact Duplicate Dr, Irvine, CA 92620. $4,600 per month. "
        "3 bedrooms 2 baths 1,700 sqft backyard attached garage."
    )
    second_text = (
        "1 Exact Duplicate Dr, Irvine, CA 92620. $4,550 per month. "
        "3 bedrooms 2 baths 1,725 sqft fenced backyard attached garage washer dryer."
    )

    with TestClient(app) as client:
        first = client.post("/api/import/clip", json=_payload(url, f"Exact Duplicate {unique}", first_text, "First note")).json()
        listing_id = first["data"]["listing_id"]
        client.patch(
            f"/api/listings/{listing_id}/decision",
            json={
                "decision_status": "contacted",
                "priority": "high",
                "next_action": "Follow up",
                "decision_reason": "Already contacted before duplicate update",
            },
        )
        client.patch(f"/api/listings/{listing_id}/notes", json={"note": "Preserved older note"})

        second = client.post("/api/import/clip", json=_payload(url, f"Exact Duplicate {unique}", second_text, "Second note"))
        listing = _listing_by_id(client, listing_id)

    assert second.status_code == 200
    assert second.json()["data"]["listing_id"] == listing_id
    assert second.json()["data"]["duplicate_status"] == "updated_existing"
    assert listing["price"] == 4550
    assert listing["decision_status"] == "contacted"
    assert any(note["note"] == "Preserved older note" for note in listing["notes"])
    assert any(note["note"] == "Second note" for note in listing["notes"])


def test_possible_duplicate_by_title_city_price_is_created_and_marked_needs_review() -> None:
    unique = uuid4().hex
    title = f"Possible Duplicate {unique}"
    first_url = f"https://www.redfin.com/CA/Irvine/possible-duplicate-a-{unique}"
    second_url = f"https://www.redfin.com/CA/Irvine/possible-duplicate-b-{unique}"
    text = (
        "Irvine CA. $4,700 per month. 3 bedrooms 2 baths 1,680 sqft. "
        "Private backyard and attached garage."
    )

    with TestClient(app) as client:
        first = client.post("/api/import/clip", json=_payload(first_url, title, text))
        second = client.post("/api/import/clip", json=_payload(second_url, title, text))
        first_id = first.json()["data"]["listing_id"]
        second_payload = second.json()
        second_listing = _listing_by_id(client, second_payload["data"]["listing_id"])

    assert first.status_code == 200
    assert second.status_code == 200
    assert second_payload["data"]["listing_id"] != first_id
    assert second_payload["data"]["duplicate_status"] == "possible_duplicate"
    assert second_payload["data"]["needs_review"] is True
    assert second_listing["decision_status"] == "needs_review"
    assert second_listing["raw_payload_json"]["possible_duplicate_listing_ids"] == [first_id]
