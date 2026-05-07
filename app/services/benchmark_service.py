from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any


BENCHMARK_PATH = Path(__file__).resolve().parent.parent / "data" / "city_benchmarks.json"
COUNTY_FALLBACK_KEY = "Orange County"
REQUIRED_FIELDS = {
    "city",
    "county",
    "state",
    "median_rent_3br",
    "typical_low_3br",
    "typical_high_3br",
    "median_price_per_sqft",
    "typical_low_price_per_sqft",
    "typical_high_price_per_sqft",
    "benchmark_confidence",
    "data_source_type",
    "data_sources",
    "last_reviewed",
    "notes",
}
CONFIDENCE_MULTIPLIER = {"high": 1.0, "medium": 0.94, "low": 0.86, "fallback": 0.78, "unknown": 0.72}


@dataclass(slots=True)
class Benchmark:
    city: str
    county: str
    state: str
    median_rent_3br: float
    typical_low_3br: float
    typical_high_3br: float
    median_price_per_sqft: float
    typical_low_price_per_sqft: float
    typical_high_price_per_sqft: float
    benchmark_confidence: str
    data_source_type: str
    data_sources: list[dict[str, Any]] = field(default_factory=list)
    last_reviewed: str | None = None
    notes: str | None = None
    requested_city: str | None = None
    used_fallback: bool = False

    @property
    def confidence_multiplier(self) -> float:
        return CONFIDENCE_MULTIPLIER.get(self.benchmark_confidence, CONFIDENCE_MULTIPLIER["unknown"])

    def source_names(self) -> list[str]:
        return [str(source.get("name")) for source in self.data_sources if source.get("name")]

    def to_context(self) -> dict[str, Any]:
        return {
            "benchmark_city": self.city,
            "requested_city": self.requested_city,
            "benchmark_used": True,
            "benchmark_used_fallback": self.used_fallback,
            "benchmark_confidence": self.benchmark_confidence,
            "benchmark_source_type": self.data_source_type,
            "median_rent_3br": self.median_rent_3br,
            "typical_low_3br": self.typical_low_3br,
            "typical_high_3br": self.typical_high_3br,
            "median_price_per_sqft": self.median_price_per_sqft,
            "typical_low_price_per_sqft": self.typical_low_price_per_sqft,
            "typical_high_price_per_sqft": self.typical_high_price_per_sqft,
            "benchmark_notes": self.notes,
            "benchmark_sources": self.data_sources,
            "last_reviewed": self.last_reviewed,
        }


def normalize_city_name(city: str | None) -> str | None:
    if not city:
        return None
    compact = re.sub(r"\s+", " ", city.strip())
    if not compact:
        return None
    known = {normalize_city_name_raw(name): name for name in load_benchmark_data().keys() if not name.startswith("_")}
    return known.get(normalize_city_name_raw(compact), compact.title())


def normalize_city_name_raw(city: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", city.lower())


@lru_cache(maxsize=1)
def load_benchmark_data() -> dict[str, Any]:
    try:
        with BENCHMARK_PATH.open(encoding="utf-8") as handle:
            data = json.load(handle)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def validate_benchmark_data(data: dict[str, Any] | None = None) -> list[str]:
    data = data if data is not None else load_benchmark_data()
    errors: list[str] = []
    if not data:
        return ["Benchmark data is missing or empty."]

    entries = {key: value for key, value in data.items() if not key.startswith("_")}
    if COUNTY_FALLBACK_KEY not in entries:
        errors.append(f"Missing county fallback benchmark: {COUNTY_FALLBACK_KEY}.")

    for key, entry in entries.items():
        if not isinstance(entry, dict):
            errors.append(f"{key}: benchmark entry must be an object.")
            continue
        missing = sorted(REQUIRED_FIELDS - set(entry.keys()))
        if missing:
            errors.append(f"{key}: missing fields {', '.join(missing)}.")
        for numeric in [
            "median_rent_3br",
            "typical_low_3br",
            "typical_high_3br",
            "median_price_per_sqft",
            "typical_low_price_per_sqft",
            "typical_high_price_per_sqft",
        ]:
            value = entry.get(numeric)
            if not isinstance(value, int | float) or value <= 0:
                errors.append(f"{key}: {numeric} must be a positive number.")
        if entry.get("benchmark_confidence") not in CONFIDENCE_MULTIPLIER:
            errors.append(f"{key}: benchmark_confidence must be one of {sorted(CONFIDENCE_MULTIPLIER)}.")
        if not isinstance(entry.get("data_sources"), list) or not entry.get("data_sources"):
            errors.append(f"{key}: data_sources must be a non-empty list.")
        low = entry.get("typical_low_3br")
        median = entry.get("median_rent_3br")
        high = entry.get("typical_high_3br")
        if all(isinstance(value, int | float) for value in [low, median, high]) and not low <= median <= high:
            errors.append(f"{key}: 3BR low/median/high range is not ordered.")
    return errors


def benchmark_from_entry(entry: dict[str, Any], *, requested_city: str | None, used_fallback: bool = False) -> Benchmark | None:
    try:
        return Benchmark(
            city=str(entry["city"]),
            county=str(entry["county"]),
            state=str(entry["state"]),
            median_rent_3br=float(entry["median_rent_3br"]),
            typical_low_3br=float(entry["typical_low_3br"]),
            typical_high_3br=float(entry["typical_high_3br"]),
            median_price_per_sqft=float(entry["median_price_per_sqft"]),
            typical_low_price_per_sqft=float(entry["typical_low_price_per_sqft"]),
            typical_high_price_per_sqft=float(entry["typical_high_price_per_sqft"]),
            benchmark_confidence=str(entry.get("benchmark_confidence") or "unknown"),
            data_source_type=str(entry.get("data_source_type") or "unknown"),
            data_sources=list(entry.get("data_sources") or []),
            last_reviewed=entry.get("last_reviewed"),
            notes=entry.get("notes"),
            requested_city=requested_city,
            used_fallback=used_fallback,
        )
    except (KeyError, TypeError, ValueError):
        return None


def get_benchmark_for_city(city: str | None) -> Benchmark | None:
    data = load_benchmark_data()
    if not data:
        return None

    requested_city = city
    normalized = normalize_city_name(city)
    entry = data.get(normalized) if normalized else None
    if isinstance(entry, dict):
        benchmark = benchmark_from_entry(entry, requested_city=requested_city, used_fallback=False)
        if benchmark:
            return benchmark

    fallback_entry = data.get(COUNTY_FALLBACK_KEY)
    if isinstance(fallback_entry, dict):
        return benchmark_from_entry(fallback_entry, requested_city=requested_city, used_fallback=True)
    return None


def clear_benchmark_cache() -> None:
    load_benchmark_data.cache_clear()
