"""Command-line entry point: ``llm-eval``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from llm_eval.config import load_config
from llm_eval.regression import Thresholds, compare, format_checks, load_baseline, save_baseline
from llm_eval.report import write_reports
from llm_eval.runner import load_run, run


def _progress(done: int, total: int) -> None:
    if done == total or done % 10 == 0:
        print(f"\r  {done}/{total} calls", end="\n" if done == total else "", file=sys.stderr)


def cmd_run(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    if args.output_dir:
        config.output_dir = args.output_dir
    print(
        f"Running '{config.name}': {len(config.suites)} suite(s) x {len(config.models)} model(s)"
        f" via {config.provider}",
        file=sys.stderr,
    )
    result = run(config, progress=_progress)
    out = result.save(config.output_dir)
    md, html = write_reports(result, out)
    with pd.option_context("display.width", 200, "display.max_columns", 20):
        print(result.summary.to_string(index=False, float_format=lambda v: f"{v:.4g}"))
    print(f"\nResults written to {out}\n  report: {md}\n  report: {html}", file=sys.stderr)

    if args.update_baseline:
        path = Path(config.regression.get("baseline") or f"baselines/{config.name}.json")
        save_baseline(result.summary, path)
        print(f"Baseline updated: {path}", file=sys.stderr)
        return 0
    if args.check:
        baseline_path = config.regression.get("baseline")
        baseline = load_baseline(Path(baseline_path)) if baseline_path else None
        return _report_checks(
            compare(result.summary, baseline, Thresholds.from_dict(config.regression)), out
        )
    return 0


def _report_checks(checks, out_dir: Path | None) -> int:
    text = format_checks(checks)
    print("\n" + text)
    if out_dir is not None:
        (out_dir / "regression.md").write_text(text, encoding="utf-8")
    return 1 if any(not c.passed for c in checks) else 0


def cmd_check(args: argparse.Namespace) -> int:
    result = load_run(args.run_dir)
    thresholds = Thresholds(
        max_accuracy_drop=args.max_accuracy_drop,
        max_json_valid_drop=args.max_json_valid_drop,
        max_cost_increase_pct=args.max_cost_increase_pct,
        min_field_accuracy=args.min_field_accuracy,
    )
    checks = compare(result.summary, load_baseline(args.baseline), thresholds)
    return _report_checks(checks, Path(args.run_dir))


def cmd_report(args: argparse.Namespace) -> int:
    result = load_run(args.run_dir)
    md, html = write_reports(result, Path(args.run_dir))
    print(f"Wrote {md} and {html}", file=sys.stderr)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="llm-eval", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="run a config and save results")
    p_run.add_argument("--config", "-c", required=True, help="path to a run config YAML")
    p_run.add_argument("--output-dir", "-o", type=Path, default=None)
    p_run.add_argument(
        "--check", action="store_true", help="fail on regressions vs the config's baseline"
    )
    p_run.add_argument(
        "--update-baseline", action="store_true", help="write this run's metrics as the baseline"
    )
    p_run.set_defaults(func=cmd_run)

    p_report = sub.add_parser("report", help="(re)build reports for a saved run directory")
    p_report.add_argument("run_dir", type=Path)
    p_report.set_defaults(func=cmd_report)

    defaults = Thresholds()
    p_check = sub.add_parser("check", help="compare a saved run against a baseline")
    p_check.add_argument("run_dir", type=Path)
    p_check.add_argument("--baseline", "-b", type=Path, required=True)
    p_check.add_argument("--max-accuracy-drop", type=float, default=defaults.max_accuracy_drop)
    p_check.add_argument("--max-json-valid-drop", type=float, default=defaults.max_json_valid_drop)
    p_check.add_argument(
        "--max-cost-increase-pct", type=float, default=defaults.max_cost_increase_pct
    )
    p_check.add_argument("--min-field-accuracy", type=float, default=defaults.min_field_accuracy)
    p_check.set_defaults(func=cmd_check)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
