from __future__ import annotations

import logging
import sys

from app.config import LOG_DIR


def configure_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger()
    if getattr(root, "_renter_configured", False):
        return

    formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    file_handler = logging.FileHandler(LOG_DIR / "renter.log", encoding="utf-8")
    file_handler.setFormatter(formatter)

    root.setLevel(logging.INFO)
    root.addHandler(stream_handler)
    root.addHandler(file_handler)
    root._renter_configured = True  # type: ignore[attr-defined]
