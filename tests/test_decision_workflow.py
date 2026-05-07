from fastapi.testclient import TestClient

from app.main import app


def test_decision_watchlist_and_notes_endpoints_work() -> None:
    with TestClient(app) as client:
        listing_id = client.get("/api/listings").json()[0]["id"]
        decision = client.patch(
            f"/api/listings/{listing_id}/decision",
            json={
                "decision_status": "contacted",
                "priority": "high",
                "next_action": "Follow up on garage details",
                "decision_reason": "Strong score and acceptable rent",
            },
        )
        watchlist = client.patch(
            f"/api/listings/{listing_id}/watchlist",
            json={"watchlist_status": "shortlist", "priority": "high", "reason": "Worth comparing"},
        )
        notes = client.patch(
            f"/api/listings/{listing_id}/notes",
            json={"note": "Ask about yard maintenance."},
        )
        breakdown = client.get(f"/api/listings/{listing_id}/score-breakdown")

    assert decision.status_code == 200
    assert decision.json()["decision_status"] == "contacted"
    assert watchlist.status_code == 200
    assert watchlist.json()["watchlist_status"] == "shortlist"
    assert notes.status_code == 200
    assert any(note["note"] == "Ask about yard maintenance." for note in notes.json()["notes"])
    assert breakdown.status_code == 200
    assert breakdown.json()["reasons"]

