"""Compare a run against a stored baseline and fail on regressions."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

BASELINE_METRICS = ["field_accuracy", "exact_match_rate", "json_valid_rate", "cost_per_doc_usd"]


@dataclass(frozen=True)
class Thresholds:
    max_accuracy_drop: float = 0.02  # absolute, e.g. 0.02 = 2 percentage points
    max_json_valid_drop: float = 0.05
    max_cost_increase_pct: float = 25.0
    min_field_accuracy: float = 0.0

    @classmethod
    def from_dict(cls, raw: dict) -> Thresholds:
        known = {k: float(v) for k, v in raw.items() if k in cls.__dataclass_fields__}
        return cls(**known)


@dataclass(frozen=True)
class Check:
    suite: str
    model: str
    metric: str
    baseline: float | None
    current: float
    limit: str
    passed: bool


def save_baseline(summary: pd.DataFrame, path: Path) -> None:
    rows = summary[["suite", "model", *BASELINE_METRICS]].to_dict(orient="records")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"metrics": rows}, indent=2) + "\n")


def load_baseline(path: Path) -> dict[tuple[str, str], dict]:
    data = json.loads(path.read_text())
    return {(r["suite"], r["model"]): r for r in data["metrics"]}


def compare(
    summary: pd.DataFrame,
    baseline: dict[tuple[str, str], dict] | None,
    thresholds: Thresholds,
) -> list[Check]:
    checks: list[Check] = []
    for row in summary.to_dict(orient="records"):
        suite, model = row["suite"], row["model"]
        acc = float(row["field_accuracy"])
        if thresholds.min_field_accuracy > 0:
            checks.append(
                Check(
                    suite,
                    model,
                    "field_accuracy (floor)",
                    None,
                    acc,
                    f">= {thresholds.min_field_accuracy:.3f}",
                    acc >= thresholds.min_field_accuracy,
                )
            )
        base = (baseline or {}).get((suite, model))
        if base is None:
            continue
        b_acc = float(base["field_accuracy"])
        checks.append(
            Check(
                suite,
                model,
                "field_accuracy",
                b_acc,
                acc,
                f"drop <= {thresholds.max_accuracy_drop:.3f}",
                acc >= b_acc - thresholds.max_accuracy_drop - 1e-9,
            )
        )
        b_json, c_json = float(base["json_valid_rate"]), float(row["json_valid_rate"])
        checks.append(
            Check(
                suite,
                model,
                "json_valid_rate",
                b_json,
                c_json,
                f"drop <= {thresholds.max_json_valid_drop:.3f}",
                c_json >= b_json - thresholds.max_json_valid_drop - 1e-9,
            )
        )
        b_cost, c_cost = float(base["cost_per_doc_usd"]), float(row["cost_per_doc_usd"])
        cost_limit = b_cost * (1 + thresholds.max_cost_increase_pct / 100)
        checks.append(
            Check(
                suite,
                model,
                "cost_per_doc_usd",
                b_cost,
                c_cost,
                f"increase <= {thresholds.max_cost_increase_pct:.0f}%",
                c_cost <= cost_limit + 1e-12,
            )
        )
    return checks


def format_checks(checks: list[Check]) -> str:
    if not checks:
        return "No regression checks were applicable (no baseline match and no floors set).\n"
    failed = [c for c in checks if not c.passed]
    head = (
        f"**Regression check: {'FAILED' if failed else 'passed'}** "
        f"({len(checks) - len(failed)}/{len(checks)} checks passed)\n\n"
    )
    lines = [
        "| | Suite | Model | Metric | Baseline | Current | Limit |",
        "|---|---|---|---|---|---|---|",
    ]
    for c in sorted(checks, key=lambda c: c.passed):
        base = "-" if c.baseline is None else f"{c.baseline:.4g}"
        mark = "✅" if c.passed else "❌"
        cells = [mark, c.suite, c.model, c.metric, base, f"{c.current:.4g}", c.limit]
        lines.append("| " + " | ".join(cells) + " |")
    return head + "\n".join(lines) + "\n"
