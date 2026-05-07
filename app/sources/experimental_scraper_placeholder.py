from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ExperimentalScraperPlaceholder:
    source_name: str
    source_type: str = "experimental_scraper"
    enabled_by_default: bool = False

    def ingest(self, _: object) -> None:
        raise RuntimeError(
            f"{self.source_name} scraper is intentionally disabled. Review source terms, robots policy, "
            "rate limits, and implementation details before activation."
        )

