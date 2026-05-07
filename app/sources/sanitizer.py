from __future__ import annotations

import re
from html import unescape


SCRIPT_STYLE_RE = re.compile(r"<\s*(script|style)[^>]*>.*?<\s*/\s*\1\s*>", re.I | re.S)
TAG_RE = re.compile(r"<[^>]+>")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def sanitize_clipped_text(value: str | None, *, max_length: int = 30_000) -> str | None:
    if value is None:
        return None
    text = unescape(value)
    text = SCRIPT_STYLE_RE.sub(" ", text)
    text = TAG_RE.sub(" ", text)
    text = CONTROL_RE.sub(" ", text)
    text = " ".join(text.split())
    if not text:
        return None
    return text[:max_length]

