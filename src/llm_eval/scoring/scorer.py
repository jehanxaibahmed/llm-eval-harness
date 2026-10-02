"""Score one model prediction against one labelled test case."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

from llm_eval.dataset import Suite, TestCase
from llm_eval.scoring.matchers import match

_MISSING = object()


@dataclass(frozen=True)
class FieldResult:
    path: str
    expected: Any
    actual: Any
    correct: bool
    matcher: str


@dataclass
class CaseScore:
    case_id: str
    json_valid: bool
    fields: list[FieldResult] = field(default_factory=list)

    @property
    def correct(self) -> int:
        return sum(f.correct for f in self.fields)

    @property
    def total(self) -> int:
        return len(self.fields)

    @property
    def accuracy(self) -> float:
        return self.correct / self.total if self.total else 0.0

    @property
    def exact_match(self) -> bool:
        return self.json_valid and self.total > 0 and self.correct == self.total


def iter_leaves(value: Any, suite: Suite, prefix: str = "") -> Iterator[tuple[str, Any]]:
    """Yield ``(path, value)`` for every scoreable leaf in an expected object."""
    if prefix and suite.rule_for(prefix).matcher == "unordered_list":
        yield prefix, value
    elif isinstance(value, dict) and value:
        for key, child in value.items():
            yield from iter_leaves(child, suite, f"{prefix}.{key}" if prefix else key)
    elif isinstance(value, list) and value:
        for idx, child in enumerate(value):
            yield from iter_leaves(child, suite, f"{prefix}[{idx}]")
    else:
        yield prefix, value


def lookup(obj: Any, path: str) -> Any:
    """Resolve a dotted/indexed path such as ``items[0].sku``; returns ``_MISSING`` if absent."""
    current = obj
    for part in path.replace("[", ".[").split("."):
        if not part:
            continue
        if part.startswith("["):
            idx = int(part[1:-1])
            if not isinstance(current, list) or idx >= len(current):
                return _MISSING
            current = current[idx]
        else:
            if not isinstance(current, dict) or part not in current:
                return _MISSING
            current = current[part]
    return current


def score_case(suite: Suite, case: TestCase, predicted: dict[str, Any] | None) -> CaseScore:
    score = CaseScore(case_id=case.id, json_valid=predicted is not None)
    for path, expected in iter_leaves(case.expected, suite):
        rule = suite.rule_for(path)
        actual = lookup(predicted, path) if predicted is not None else _MISSING
        correct = actual is not _MISSING and match(expected, actual, rule)
        score.fields.append(
            FieldResult(
                path=path,
                expected=expected,
                actual=None if actual is _MISSING else actual,
                correct=correct,
                matcher=rule.matcher,
            )
        )
    return score
