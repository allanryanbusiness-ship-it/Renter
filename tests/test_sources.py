from app.schemas import CsvImportRequest, PasteImportRequest
from app.sources.csv_import import CsvImportAdapter, canonical_column
from app.sources.paste_import import PasteImportAdapter
from app.sources.url_reference import infer_source_from_url


def test_source_inference_from_common_urls() -> None:
    assert infer_source_from_url("https://www.zillow.com/homedetails/example") == "Zillow"
    assert infer_source_from_url("https://redfin.com/CA/Irvine/example") == "Redfin"
    assert infer_source_from_url("https://orangecounty.craigslist.org/apa/example") == "Craigslist"


def test_paste_import_parser_extracts_core_fields_and_evidence() -> None:
    payload = PasteImportRequest(
        raw_text=(
            "Irvine detached rental\n"
            "$4,650 per month\n"
            "3 bedrooms 2.5 baths 1,850 sqft\n"
            "Attached two-car garage and fenced backyard. Dogs considered. Washer dryer included."
        ),
        source_url="https://www.zillow.com/homedetails/example",
        notes="Candidate pasted by user.",
    )

    result = PasteImportAdapter().ingest(payload)

    assert result.rows_imported == 1
    listing = result.listings[0]
    assert listing.price_monthly == 4650
    assert listing.bedrooms == 3
    assert listing.bathrooms == 2.5
    assert listing.square_feet == 1850
    assert listing.city == "Irvine"
    assert listing.backyard_status == "yes"
    assert listing.garage_status == "yes"
    assert "garage" in listing.garage_evidence.lower()


def test_paste_import_parser_detects_extended_evidence_terms() -> None:
    payload = PasteImportRequest(
        raw_text=(
            "Costa Mesa lease $4,100 monthly. 3 bed 2 bath 1,600 sqft. "
            "Private garden deck and covered parking carport are included."
        )
    )

    result = PasteImportAdapter().ingest(payload)
    listing = result.listings[0]

    assert listing.backyard_status == "yes"
    assert "garden" in listing.backyard_evidence.lower()
    assert listing.garage_status == "yes"
    assert "carport" in listing.garage_evidence.lower()



def test_csv_import_maps_common_columns_and_preserves_unknowns() -> None:
    csv_text = (
        "name,city,rent,beds,baths,sqft,yard,garage,custom_flag\n"
        'Tustin Lease,Tustin,"$4,300",3,2.5,1700,yes,unknown,from-export\n'
    )
    result = CsvImportAdapter().ingest(CsvImportRequest(csv_text=csv_text))

    assert canonical_column("monthly rent") == "price_monthly"
    assert result.rows_received == 1
    assert result.rows_imported == 1
    listing = result.listings[0]
    assert listing.title == "Tustin Lease"
    assert listing.backyard_status == "yes"
    assert listing.garage_status == "unknown"
    assert listing.provenance.raw_payload_json["unknown_columns"]["custom_flag"] == "from-export"
