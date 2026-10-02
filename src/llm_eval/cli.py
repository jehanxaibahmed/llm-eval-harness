"""Command-line entry point: ``llm-eval``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from llm_eval.config import load_config
from llm_eval.runner import run


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
    with pd.option_context("display.width", 200, "display.max_columns", 20):
        print(result.summary.to_string(index=False, float_format=lambda v: f"{v:.4g}"))
    print(f"\nResults written to {out}", file=sys.stderr)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="llm-eval", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="run a config and save results")
    p_run.add_argument("--config", "-c", required=True, help="path to a run config YAML")
    p_run.add_argument("--output-dir", "-o", type=Path, default=None)
    p_run.set_defaults(func=cmd_run)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
