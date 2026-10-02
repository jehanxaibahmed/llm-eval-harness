from __future__ import annotations

from llm_eval.report.insights import Insights


def pct(v: float) -> str:
    return f"{v * 100:.1f}%"


def usd(v: float) -> str:
    return f"${v:.5f}" if v < 0.01 else f"${v:.4f}"


def secs(v: float) -> str:
    return f"{v:.2f}s"


def _table(headers: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    lines += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(lines)


def render_markdown(ins: Insights) -> str:
    out = [
        f"# Eval report: {ins.config_name}",
        "",
        f"Run `{ins.run_id}` · started {ins.started_at[:19].replace('T', ' ')} UTC"
        f" · {len(ins.models)} models"
        f" · {len(ins.suites)} suites",
        "",
        "## Overall",
        "",
        _table(
            ["Model", "Field accuracy", "Exact match", "Valid JSON", "Latency p50", "Total cost"],
            [
                [
                    r.model,
                    pct(r.field_accuracy),
                    pct(r.exact_match_rate),
                    pct(r.json_valid_rate),
                    secs(r.latency_p50_s),
                    usd(r.total_cost_usd),
                ]
                for r in ins.overall.itertuples()
            ],
        ),
    ]
    for suite in ins.suites:
        out += ["", f"## Suite: {suite.name}", ""]
        if suite.picks:
            out += [" · ".join(f"**{k}:** {v}" for k, v in suite.picks.items()), ""]
        out.append(
            _table(
                [
                    "Model",
                    "Field acc.",
                    "Exact match",
                    "Valid JSON",
                    "p50",
                    "p95",
                    "Cost/doc",
                    "Errors",
                ],
                [
                    [
                        r.model,
                        pct(r.field_accuracy),
                        pct(r.exact_match_rate),
                        pct(r.json_valid_rate),
                        secs(r.latency_p50_s),
                        secs(r.latency_p95_s),
                        usd(r.cost_per_doc_usd),
                        str(r.errors),
                    ]
                    for r in suite.summary.itertuples()
                ],
            )
        )
        out += ["", "### Weakest fields", ""]
        for model, df in suite.weakest_fields.items():
            items = ", ".join(f"`{r.field}` {pct(r.accuracy)}" for r in df.itertuples())
            items = items or "every field 100% correct"
            out.append(f"- **{model}**: {items}")
        if not suite.failures.empty:
            out += ["", "### Lowest-scoring cases", ""]
            out.append(
                _table(
                    ["Model", "Case", "Accuracy", "Valid JSON", "Error"],
                    [
                        [
                            r.model,
                            f"`{r.case_id}`",
                            pct(r.accuracy),
                            "yes" if r.json_valid else "no",
                            r.error if isinstance(r.error, str) else "",
                        ]
                        for r in suite.failures.itertuples()
                    ],
                )
            )
    return "\n".join(out) + "\n"
