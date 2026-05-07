from app.sources.source_inference import infer_source_from_url, normalize_domain


def test_source_inference_recognizes_common_listing_domains() -> None:
    assert infer_source_from_url("https://www.zillow.com/homedetails/demo") == "Zillow"
    assert infer_source_from_url("https://redfin.com/CA/Irvine/demo") == "Redfin"
    assert infer_source_from_url("https://www.realtor.com/realestateandhomes-detail/demo") == "Realtor"
    assert infer_source_from_url("https://www.apartments.com/demo") == "Apartments.com"
    assert infer_source_from_url("https://hotpads.com/demo") == "HotPads"
    assert infer_source_from_url("https://orangecounty.craigslist.org/apa/demo") == "Craigslist"
    assert infer_source_from_url("https://www.facebook.com/marketplace/item/demo") == "Facebook Marketplace"
    assert infer_source_from_url("https://marketplace.facebook.com/item/demo") == "Facebook Marketplace"


def test_source_inference_flags_property_manager_domains() -> None:
    assert infer_source_from_url("https://www.example-property-management.com/listings/1") == "Property Management Site"
    assert infer_source_from_url("https://irvineleasing.example.com/homes/1") == "Property Management Site"
    assert infer_source_from_url("https://example.com/listings/1") == "Other"


def test_normalize_domain_accepts_domain_or_url() -> None:
    assert normalize_domain("https://www.zillow.com/homedetails/demo") == "zillow.com"
    assert normalize_domain("www.redfin.com") == "redfin.com"
