from pathlib import Path

import pytest

from llm_eval.analysis import field_accuracy, summarize
from llm_eval.cli import main
from llm_eval.config import load_config
from llm_eval.runner import run

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def config(tmp_path):
    cfg = load_config(ROOT / "configs" / "mock.yaml")
    cfg.output_dir = tmp_path
    return cfg


def test_config_resolves_paths(config):
    assert all(p.exists() for p in config.suites)
    assert [m.label for m in config.models][0] == "precise-large"


def test_mock_run_end_to_end(config):
    result = run(config)
    n_cases = 24
    assert len(result.cases) == n_cases * len(config.models)
    summary = result.summary
    assert set(summary["model"]) == {"precise-large", "balanced-medium", "fast-small"}
    acc = summary.groupby("model")["field_accuracy"].mean()
    # profiles are ordered by quality
    assert acc["precise-large"] > acc["balanced-medium"] > acc["fast-small"]
    assert (summary["total_cost_usd"] > 0).all()

    out = result.save(config.output_dir)
    for name in ("cases.csv", "fields.csv", "summary.csv", "raw.jsonl", "run.json"):
        assert (out / name).exists()


def test_run_is_reproducible(config):
    a, b = run(config), run(config)
    cols = ["suite", "model", "case_id", "fields_correct", "cost_usd"]
    assert a.cases[cols].equals(b.cases[cols])


def test_field_accuracy_collapses_indices(config):
    fa = field_accuracy(run(config).fields)
    assert "items[].sku" in set(fa["field"])


def test_summarize_empty():
    import pandas as pd

    assert summarize(pd.DataFrame()).empty


def test_cli_run(tmp_path, capsys):
    assert main(["run", "-c", str(ROOT / "configs" / "mock.yaml"), "-o", str(tmp_path)]) == 0
    assert "precise-large" in capsys.readouterr().out
    assert any(tmp_path.iterdir())
