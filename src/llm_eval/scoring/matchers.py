"""Value comparison strategies used for field-level scoring."""

from __future__ import annotations

import re
from collections import Counter
from datetime import date, datetime
from typing import Any

from llm_eval.dataset import FieldRule

_DATE_FORMATS = (
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%d.%m.%Y",
    "%d %B %Y",
    "%d %b %Y",
    "%B %d, %Y",
    "%b %d, %Y",
    "%Y/%m/%d",
)
_NUM_CLEAN = re.compile(r"[^\d.\-eE]")


def normalize(value: Any) -> str:
    return " ".join(str(value).strip().lower().split())


def to_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        cleaned = _NUM_CLEAN.sub("", value)
        if cleaned in {"", "-", "."}:
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def to_date(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        return None
    text = value.strip()
    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        pass
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def match(expected: Any, actual: Any, rule: FieldRule) -> bool:
    if expected is None or actual is None:
        return expected is None and actual is None

    if rule.matcher == "exact":
        return expected == actual
    if rule.matcher == "numeric":
        e, a = to_number(expected), to_number(actual)
        return e is not None and a is not None and abs(e - a) <= rule.tolerance + 1e-9
    if rule.matcher == "date":
        e, a = to_date(expected), to_date(actual)
        return e is not None and e == a
    if rule.matcher == "unordered_list":
        if not isinstance(expected, list) or not isinstance(actual, list):
            return False
        return Counter(map(normalize, expected)) == Counter(map(normalize, actual))

    # normalized: numbers compare numerically, everything else as cleaned strings
    if isinstance(expected, int | float) and not isinstance(expected, bool):
        a = to_number(actual)
        return a is not None and abs(float(expected) - a) <= 1e-9
    return normalize(expected) == normalize(actual)
