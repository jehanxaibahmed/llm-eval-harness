"""Side-by-side model comparison reports (Markdown and self-contained HTML)."""

from __future__ import annotations

from pathlib import Path

from llm_eval.report.html import render_html
from llm_eval.report.insights import Insights, build_insights
from llm_eval.report.markdown import render_markdown
from llm_eval.runner import RunResult


def write_reports(result: RunResult, out_dir: Path) -> tuple[Path, Path]:
    insights = build_insights(result)
    md_path = out_dir / "report.md"
    html_path = out_dir / "report.html"
    md_path.write_text(render_markdown(insights), encoding="utf-8")
    html_path.write_text(render_html(insights), encoding="utf-8")
    return md_path, html_path


__all__ = ["Insights", "build_insights", "render_html", "render_markdown", "write_reports"]
