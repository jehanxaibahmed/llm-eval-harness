"""Labelled test-set format and loaders.

A suite lives in its own directory::

    evals/<suite>/
        suite.yaml     # name, description, prompt file, per-field match rules
        prompt.md      # prompt template; ``{input}`` is replaced with the document
        cases.jsonl    # one JSON object per line: {"id", "input", "expected", "tags"?}
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

MATCHERS = {"exact", "normalized", "numeric", "date", "unordered_list"}


class DatasetError(ValueError):
    """Raised when a suite or test case is malformed."""


@dataclass(frozen=True)
class FieldRule:
    """How a single expected field is compared against model output."""

    matcher: str = "normalized"
    tolerance: float = 0.0

    def __post_init__(self) -> None:
        if self.matcher not in MATCHERS:
            raise DatasetError(
                f"unknown matcher {self.matcher!r}; expected one of {sorted(MATCHERS)}"
            )


@dataclass(frozen=True)
class TestCase:
    __test__ = False  # not a pytest test class

    id: str
    input: str
    expected: dict[str, Any]
    tags: tuple[str, ...] = ()


@dataclass
class Suite:
    name: str
    description: str
    prompt_template: str
    cases: list[TestCase]
    field_rules: dict[str, FieldRule] = field(default_factory=dict)

    def rule_for(self, path: str) -> FieldRule:
        """Rule for a dotted field path, falling back to its top-level key, then the default."""
        if path in self.field_rules:
            return self.field_rules[path]
        # list items like "items[0].sku" share the rule for "items.sku"
        generic = _strip_indices(path)
        return self.field_rules.get(generic, FieldRule())

    def render_prompt(self, case: TestCase) -> str:
        return self.prompt_template.replace("{input}", case.input)


def _strip_indices(path: str) -> str:
    out, depth = [], 0
    for ch in path:
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
        elif depth == 0:
            out.append(ch)
    return "".join(out)


def load_cases(path: Path) -> list[TestCase]:
    cases: list[TestCase] = []
    seen: set[str] = set()
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise DatasetError(f"{path}:{lineno}: invalid JSON ({exc.msg})") from exc
        for key in ("id", "input", "expected"):
            if key not in raw:
                raise DatasetError(f"{path}:{lineno}: missing required key {key!r}")
        if not isinstance(raw["expected"], dict):
            raise DatasetError(f"{path}:{lineno}: 'expected' must be a JSON object")
        if raw["id"] in seen:
            raise DatasetError(f"{path}:{lineno}: duplicate case id {raw['id']!r}")
        seen.add(raw["id"])
        cases.append(
            TestCase(
                id=str(raw["id"]),
                input=str(raw["input"]),
                expected=raw["expected"],
                tags=tuple(raw.get("tags", ())),
            )
        )
    if not cases:
        raise DatasetError(f"{path}: no test cases found")
    return cases


def load_suite(directory: str | Path) -> Suite:
    directory = Path(directory)
    meta_path = directory / "suite.yaml"
    if not meta_path.exists():
        raise DatasetError(f"{directory}: missing suite.yaml")
    meta = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}

    prompt_file = directory / meta.get("prompt", "prompt.md")
    if not prompt_file.exists():
        raise DatasetError(f"{directory}: prompt file {prompt_file.name} not found")
    template = prompt_file.read_text(encoding="utf-8")
    if "{input}" not in template:
        raise DatasetError(f"{prompt_file}: template must contain an {{input}} placeholder")

    rules = {
        name: FieldRule(**(spec if isinstance(spec, dict) else {"matcher": spec}))
        for name, spec in (meta.get("fields") or {}).items()
    }
    return Suite(
        name=meta.get("name", directory.name),
        description=meta.get("description", ""),
        prompt_template=template,
        cases=load_cases(directory / meta.get("cases", "cases.jsonl")),
        field_rules=rules,
    )
