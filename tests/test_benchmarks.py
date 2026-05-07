from app.services.benchmark_service import (
    clear_benchmark_cache,
    get_benchmark_for_city,
    normalize_city_name,
    validate_benchmark_data,
)


def test_benchmark_json_shape_is_valid() -> None:
    clear_benchmark_cache()

    assert validate_benchmark_data() == []


def test_city_name_normalization_finds_known_city() -> None:
    clear_benchmark_cache()

    assert normalize_city_name(" irvine ") == "Irvine"
    assert normalize_city_name("MISSION   VIEJO") == "Mission Viejo"


def test_missing_city_uses_county_fallback() -> None:
    clear_benchmark_cache()

    benchmark = get_benchmark_for_city("Laguna Beach")

    assert benchmark is not None
    assert benchmark.city == "Orange County"
    assert benchmark.used_fallback is True
    assert benchmark.benchmark_confidence == "fallback"


def test_benchmark_source_notes_are_preserved() -> None:
    clear_benchmark_cache()

    benchmark = get_benchmark_for_city("Irvine")

    assert benchmark is not None
    assert benchmark.data_sources
    assert "Apartments.com" in benchmark.data_sources[0]["name"]
    assert benchmark.notes
