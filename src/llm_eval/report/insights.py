"""Turn raw run results into the facts both report formats render."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from llm_eval.analysis import field_accuracy
from llm_eval.runner import RunResult


@dataclass
class SuiteInsights:
    name: str
    summary: pd.DataFrame
    weakest_fields: dict[str, pd.DataFrame]
    failures: pd.DataFrame
    picks: dict[str, str] = field(default_factory=dict)


@dataclass
class Insights:
    run_id: str
    config_name: str
    started_at: str
    models: list[str]
    overall: pd.DataFrame
    suites: list[SuiteInsights]


def _picks(summary: pd.DataFrame, value_margin: float = 0.05) -> dict[str, str]:
    if summary.empty:
        return {}
    s = summary.set_index("model")
    picks = {
        "Most accurate": s["field_accuracy"].idxmax(),
        "Cheapest": s["cost_per_doc_usd"].idxmin(),
        "Fastest (p50)": s["latency_p50_s"].idxmin(),
    }
    # cheapest model whose accuracy is within `value_margin` of the best
    near_best = s[s["field_accuracy"] >= s["field_accuracy"].max() - value_margin]
    picks[f"Best value (within {value_margin * 100:.0f} pts)"] = near_best[
        "cost_per_doc_usd"
    ].idxmin()
    return picks


def build_insights(result: RunResult, top_n_fields: int = 5, max_failures: int = 10) -> Insights:
    summary = result.summary
    fa = field_accuracy(result.fields)
    models = list(dict.fromkeys(result.cases["model"])) if not result.cases.empty else []

    overall = (
        result.cases.groupby("model", sort=False)
        .agg(
            fields_correct=("fields_correct", "sum"),
            fields_total=("fields_total", "sum"),
            exact_match_rate=("exact_match", "mean"),
            json_valid_rate=("json_valid", "mean"),
            latency_p50_s=("latency_s", "median"),
            total_cost_usd=("cost_usd", "sum"),
        )
        .reset_index()
    )
    overall["field_accuracy"] = overall["fields_correct"] / overall["fields_total"]
    overall = overall.drop(columns=["fields_correct", "fields_total"]).sort_values(
        "field_accuracy", ascending=False
    )

    suites = []
    for suite_name, suite_summary in summary.groupby("suite", sort=False):
        suite_fa = fa[fa["suite"] == suite_name]
        weakest = {
            model: grp[grp["accuracy"] < 1].nsmallest(top_n_fields, "accuracy")[
                ["field", "accuracy"]
            ]
            for model, grp in suite_fa.groupby("model", sort=False)
        }
        cases = result.cases[result.cases["suite"] == suite_name]
        failures = (
            cases[~cases["exact_match"]]
            .sort_values("accuracy")
            .head(max_failures)[["model", "case_id", "accuracy", "json_valid", "error"]]
        )
        suites.append(
            SuiteInsights(
                name=suite_name,
                summary=suite_summary.reset_index(drop=True),
                weakest_fields=weakest,
                failures=failures,
                picks=_picks(suite_summary),
            )
        )
    return Insights(
        run_id=result.run_id,
        config_name=result.config_name,
        started_at=result.started_at,
        models=models,
        overall=overall,
        suites=suites,
    )
