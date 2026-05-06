from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class AdapterDescriptor:
    key: str
    label: str
    enabled: bool
    risk_level: str
    notes: str


class SourceAdapter(Protocol):
    descriptor: AdapterDescriptor

    def enabled(self) -> bool:
        ...


class DisabledSourceAdapter:
    def __init__(self, key: str, label: str, notes: str) -> None:
        self.descriptor = AdapterDescriptor(
            key=key,
            label=label,
            enabled=False,
            risk_level="high",
            notes=notes,
        )

    def enabled(self) -> bool:
        return False


HIGH_RISK_ADAPTERS = [
    DisabledSourceAdapter(
        "zillow_html",
        "Zillow HTML Scraper",
        "Disabled by default due to compliance and anti-bot risk.",
    ),
    DisabledSourceAdapter(
        "redfin_unofficial",
        "Redfin Unofficial Adapter",
        "Disabled by default pending approved or licensed access.",
    ),
    DisabledSourceAdapter(
        "realtor_html",
        "Realtor.com Scraper",
        "Disabled by default pending explicit permission or licensed access.",
    ),
]

