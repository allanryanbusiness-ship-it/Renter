from __future__ import annotations

import re
from typing import Any


OC_CITIES = [
    "Aliso Viejo",
    "Anaheim",
    "Brea",
    "Buena Park",
    "Costa Mesa",
    "Cypress",
    "Dana Point",
    "Fountain Valley",
    "Fullerton",
    "Garden Grove",
    "Huntington Beach",
    "Irvine",
    "Laguna Beach",
    "Laguna Hills",
    "Laguna Niguel",
    "Laguna Woods",
    "La Habra",
    "Lake Forest",
    "Los Alamitos",
    "Mission Viejo",
    "Newport Beach",
    "Orange",
    "Placentia",
    "Rancho Santa Margarita",
    "San Clemente",
    "San Juan Capistrano",
    "Santa Ana",
    "Seal Beach",
    "Stanton",
    "Tustin",
    "Villa Park",
    "Westminster",
    "Yorba Linda",
]


def clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = " ".join(str(value).split())
    return text or None


def parse_money(value: Any) -> float | None:
    if value is None:
        return None
    match = re.search(r"\$?\s*([0-9][0-9,]*(?:\.\d{1,2})?)", str(value))
    if not match:
        return None
    return float(match.group(1).replace(",", ""))


def parse_int(value: Any) -> int | None:
    if value is None:
        return None
    match = re.search(r"([0-9][0-9,]*)", str(value))
    if not match:
        return None
    return int(match.group(1).replace(",", ""))


def parse_float(value: Any) -> float | None:
    if value is None:
        return None
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)", str(value))
    if not match:
        return None
    return float(match.group(1))


def bool_from_text(value: Any) -> bool | None:
    if value is None:
        return None
    normalized = str(value).strip().lower()
    if normalized in {"yes", "y", "true", "1", "allowed", "available"}:
        return True
    if normalized in {"no", "n", "false", "0", "none", "not allowed"}:
        return False
    return None


def find_evidence(text: str, keywords: list[str]) -> str | None:
    compact = " ".join(text.split())
    sentences = re.split(r"(?<=[.!?])\s+|\n+", compact)
    for sentence in sentences:
        lowered = sentence.lower()
        if any(keyword in lowered for keyword in keywords):
            return sentence[:280]
    return None


def infer_oc_city(text: str) -> str | None:
    lowered = text.lower()
    for city in OC_CITIES:
        if city.lower() in lowered:
            return city
    match = re.search(r"\b([A-Z][A-Za-z]+(?:\s[A-Z][A-Za-z]+)?)\s*,\s*(CA|California)\b", text)
    if match:
        return match.group(1)
    return None


def infer_feature_status(text: str, positive: list[str], negative: list[str]) -> tuple[str, str | None]:
    lowered = text.lower()
    negative_evidence = find_evidence(text, negative)
    if any(term in lowered for term in negative):
        return "no", negative_evidence
    positive_evidence = find_evidence(text, positive)
    if any(term in lowered for term in positive):
        return "yes", positive_evidence
    return "unknown", None

