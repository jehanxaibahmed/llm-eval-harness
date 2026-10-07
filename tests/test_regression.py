from pathlib import Path

import pandas as pd

from llm_eval.cli import main
from llm_eval.regression import Thresholds, compare, format_checks, load_baseline, save_baseline

ROOT = Path(__file__).resolve().parent.parent


def _summary(acc=0.9, json_ok=1.0, cost=0.001):
    return pd.DataFrame(
        [
            {
                "suite": "s",
                "model": "m",
                "field_accuracy": acc,
                "exact_match_rate": 0.5,
                "json_valid_rate": json_ok,
                "cost_per_doc_usd": cost,
            }
        ]
    )


def test_baseline_roundtrip(tmp_path):
    save_baseline(_summary(), tmp_path / "b.json")
    assert load_baseline(tmp_path / "b.json")[("s", "m")]["field_accuracy"] == 0.9


def test_no_regression_passes(tmp_path):
    save_baseline(_summary(), tmp_path / "b.json")
    checks = compare(_summary(acc=0.885), load_baseline(tmp_path / "b.json"), Thresholds())
    assert all(c.passed for c in checks)


def test_accuracy_drop_fails(tmp_path):
    save_baseline(_summary(), tmp_path / "b.json")
    checks = compare(_summary(acc=0.85), load_baseline(tmp_path / "b.json"), Thresholds())
    failed = {c.metric for c in checks if not c.passed}
    assert failed == {"field_accuracy"}
    assert "FAILED" in format_checks(checks)


def test_cost_and_json_regressions(tmp_path):
    save_baseline(_summary(), tmp_path / "b.json")
    checks = compare(
        _summary(json_ok=0.8, cost=0.002), load_baseline(tmp_path / "b.json"), Thresholds()
    )
    failed = {c.metric for c in checks if not c.passed}
    assert failed == {"json_valid_rate", "cost_per_doc_usd"}


def test_floor_without_baseline():
    checks = compare(_summary(acc=0.4), None, Thresholds(min_field_accuracy=0.5))
    assert len(checks) == 1 and not checks[0].passed


def test_committed_baseline_matches_simulator_run(tmp_path):
    """CI guard: the offline run must pass against the committed baseline."""
    config = ROOT / "configs" / "simulator.yaml"
    assert main(["run", "-c", str(config), "-o", str(tmp_path), "--check"]) == 0


def test_cli_check_detects_regression(tmp_path):
    main(["run", "-c", str(ROOT / "configs" / "simulator.yaml"), "-o", str(tmp_path)])
    run_dir = next(tmp_path.iterdir())
    # an impossible floor must fail
    rc = main(
        [
            "check",
            str(run_dir),
            "-b",
            str(ROOT / "baselines/simulator.json"),
            "--min-field-accuracy",
            "0.99",
        ]
    )
    assert rc == 1
    assert (run_dir / "regression.md").exists()
