"""Pandas aggregations over per-case results."""

from __future__ import annotations

import pandas as pd

SUMMARY_COLUMNS = [
    "suite",
    "model",
    "cases",
    "field_accuracy",
    "exact_match_rate",
    "json_valid_rate",
    "latency_p50_s",
    "latency_p95_s",
    "cost_per_doc_usd",
    "total_cost_usd",
    "errors",
]


def summarize(cases: pd.DataFrame) -> pd.DataFrame:
    """One row per (suite, model) with accuracy, latency and cost metrics."""
    if cases.empty:
        return pd.DataFrame(columns=SUMMARY_COLUMNS)
    grouped = cases.groupby(["suite", "model"], sort=False)
    out = grouped.agg(
        cases=("case_id", "count"),
        fields_correct=("fields_correct", "sum"),
        fields_total=("fields_total", "sum"),
        exact_match_rate=("exact_match", "mean"),
        json_valid_rate=("json_valid", "mean"),
        latency_p50_s=("latency_s", "median"),
        latency_p95_s=("latency_s", lambda s: s.quantile(0.95)),
        cost_per_doc_usd=("cost_usd", "mean"),
        total_cost_usd=("cost_usd", "sum"),
        errors=("error", lambda s: int(s.notna().sum())),
    ).reset_index()
    out["field_accuracy"] = out["fields_correct"] / out["fields_total"].where(
        out["fields_total"] > 0
    )
    return out[SUMMARY_COLUMNS]


def field_accuracy(fields: pd.DataFrame) -> pd.DataFrame:
    """Accuracy per generic field (list indices collapsed) for each suite and model."""
    if fields.empty:
        return pd.DataFrame(columns=["suite", "field", "model", "accuracy"])
    generic = fields["field"].str.replace(r"\[\d+\]", "[]", regex=True)
    return (
        fields.assign(field=generic)
        .groupby(["suite", "field", "model"], sort=False)["correct"]
        .mean()
        .rename("accuracy")
        .reset_index()
    )
