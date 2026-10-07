from pathlib import Path

import pytest

from llm_eval.cli import main
from llm_eval.config import load_config
from llm_eval.report import build_insights, render_html, render_markdown, write_reports
from llm_eval.runner import load_run, run

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def result():
    return run(load_config(ROOT / "configs" / "simulator.yaml"))


def test_insights_picks(result):
    ins = build_insights(result)
    assert [s.name for s in ins.suites] == ["order_extraction", "invoice_extraction"]
    picks = ins.suites[0].picks
    assert picks["Most accurate"] == "precise-large"
    assert picks["Cheapest"] == "fast-small"
    assert picks["Fastest (p50)"] == "fast-small"
    assert picks["Best value (within 5 pts)"] == "precise-large"
    assert ins.overall.iloc[0]["model"] == "precise-large"


def test_markdown_contains_tables(result):
    md = render_markdown(build_insights(result))
    assert md.startswith("# Eval report: simulator")
    assert "## Suite: invoice_extraction" in md
    assert "| precise-large |" in md
    assert "### Weakest fields" in md


def test_html_is_self_contained(result):
    html = render_html(build_insights(result))
    assert html.startswith("<!doctype html>")
    assert 'class="bar"' in html and "data-tip=" in html
    assert "prefers-color-scheme:dark" in html
    assert "http://" not in html and "https://" not in html


def test_reports_rebuild_from_saved_run(result, tmp_path):
    out = result.save(tmp_path)
    loaded = load_run(out)
    assert loaded.summary.round(6).equals(result.summary.round(6))
    md, html = write_reports(loaded, out)
    assert md.exists() and html.exists()
    assert main(["report", str(out)]) == 0
