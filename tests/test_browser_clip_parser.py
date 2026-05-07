from app.schemas import BrowserClipRequest
from app.sources.browser_clip import BrowserClipAdapter, extracted_fields_for
from app.sources.sanitizer import sanitize_clipped_text


def test_browser_clip_parser_extracts_fields_and_preserves_evidence() -> None:
    result = BrowserClipAdapter().ingest(
        BrowserClipRequest(
            source_url="https://www.zillow.com/homedetails/parser-demo",
            page_title="Irvine backyard home",
            selected_text=(
                "118 Compass Rose Dr, Irvine, CA 92620. $4,650 per month. "
                "3 bedrooms 2.5 baths 1,850 sqft. Fenced backyard with patio. "
                "Attached two-car garage. Washer dryer included. Central air. Dogs considered."
            ),
            source_domain="zillow.com",
            user_notes="Parser fixture",
        )
    )

    assert result.rows_imported == 1
    listing = result.listings[0]
    fields = extracted_fields_for(listing)

    assert listing.address == "118 Compass Rose Dr"
    assert listing.city == "Irvine"
    assert listing.state == "CA"
    assert listing.zip == "92620"
    assert listing.price_monthly == 4650
    assert listing.bedrooms == 3
    assert listing.bathrooms == 2.5
    assert listing.square_feet == 1850
    assert listing.backyard_status == "yes"
    assert "Fenced backyard" in listing.backyard_evidence
    assert listing.garage_status == "yes"
    assert "Attached two-car garage" in listing.garage_evidence
    assert "parking_details" in fields
    assert "air_conditioning" in fields


def test_sanitizer_removes_html_script_and_control_chars() -> None:
    sanitized = sanitize_clipped_text("<h1>Safe</h1><script>alert(1)</script>Text\x00")

    assert sanitized == "Safe Text"
