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


def test_build_provider_openai_compatible(tmp_path):
    from llm_eval.config import load_config
    from llm_eval.runner import build_provider

    cfg = tmp_path / "c.yaml"
    cfg.write_text(
        "provider: openai_compatible\nbase_url: http://localhost:11434/v1\n"
        "suites: [s]\nmodels: [llama3.1:8b]\n"
    )
    config = load_config(cfg)
    assert config.base_url == "http://localhost:11434/v1" and config.api_key_env is None
    provider = build_provider(config, [])
    assert provider.url == "http://localhost:11434/v1/chat/completions"


def test_openai_compatible_requires_base_url(tmp_path):
    import pytest

    from llm_eval.config import load_config

    cfg = tmp_path / "c.yaml"
    cfg.write_text("provider: openai_compatible\nsuites: [s]\nmodels: [m]\n")
    with pytest.raises(ValueError, match="base_url"):
        load_config(cfg)


def test_ollama_config_models():
    from pathlib import Path

    from llm_eval.config import load_config

    config = load_config(Path(__file__).parent.parent / "configs" / "ollama.yaml")
    ids = [m.id for m in config.models]
    assert ids == ["qwen2.5:14b-instruct", "qwen2.5:32b-instruct", "llama3.1:8b", "gemma2:9b"]
    assert not any("deepseek" in i for i in ids)
