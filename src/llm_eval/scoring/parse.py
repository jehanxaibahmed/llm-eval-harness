"""Pull a JSON object out of raw model output."""

from __future__ import annotations

import json
import re
from typing import Any

_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def extract_json(text: str) -> dict[str, Any] | None:
    """Return the first JSON object found in ``text``, or ``None`` if there is none.

    Handles bare JSON, fenced ```json blocks, and JSON surrounded by prose.
    """
    candidates = [m.group(1) for m in _FENCE.finditer(text)] + [text]
    for candidate in candidates:
        candidate = candidate.strip()
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            value = _scan_for_object(candidate)
        if isinstance(value, dict):
            return value
    return None


def _scan_for_object(text: str) -> Any:
    decoder = json.JSONDecoder()
    for idx, ch in enumerate(text):
        if ch != "{":
            continue
        try:
            value, _ = decoder.raw_decode(text, idx)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    return None
