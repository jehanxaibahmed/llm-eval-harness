"""Run every case of every suite through every model and collect scored results."""

from __future__ import annotations

import json
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from llm_eval.analysis import summarize
from llm_eval.config import RunConfig
from llm_eval.dataset import Suite, TestCase, load_suite
from llm_eval.providers import MockProvider, OpenRouterProvider, Provider
from llm_eval.scoring import extract_json, score_case

ProgressFn = Callable[[int, int], None]


@dataclass
class RunResult:
    run_id: str
    config_name: str
    started_at: str
    cases: pd.DataFrame
    fields: pd.DataFrame
    raw: list[dict] = field(default_factory=list)

    @property
    def summary(self) -> pd.DataFrame:
        return summarize(self.cases)

    def save(self, output_dir: Path) -> Path:
        out = output_dir / self.run_id
        out.mkdir(parents=True, exist_ok=True)
        self.cases.to_csv(out / "cases.csv", index=False)
        self.fields.to_csv(out / "fields.csv", index=False)
        self.summary.to_csv(out / "summary.csv", index=False)
        with (out / "raw.jsonl").open("w", encoding="utf-8") as fh:
            for row in self.raw:
                fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
        meta = {"run_id": self.run_id, "config": self.config_name, "started_at": self.started_at}
        (out / "run.json").write_text(json.dumps(meta, indent=2))
        return out


def build_provider(config: RunConfig, suites: list[Suite]) -> Provider:
    if config.provider == "openrouter":
        return OpenRouterProvider(prices=config.prices)
    oracle = {s.render_prompt(c): c.expected for s in suites for c in s.cases}
    return MockProvider(oracle, seed=config.seed)


def run(
    config: RunConfig,
    provider: Provider | None = None,
    progress: ProgressFn | None = None,
) -> RunResult:
    suites = [load_suite(p) for p in config.suites]
    provider = provider or build_provider(config, suites)
    started = datetime.now(UTC)

    jobs: list[tuple[Suite, TestCase, str, str]] = [
        (suite, case, model.id, model.label)
        for suite in suites
        for model in config.models
        for case in suite.cases
    ]
    done = 0
    lock = threading.Lock()

    def execute(job: tuple[Suite, TestCase, str, str]) -> tuple[dict, list[dict], dict]:
        nonlocal done
        suite, case, model_id, label = job
        completion = provider.complete(model_id, suite.render_prompt(case))
        predicted = extract_json(completion.text) if completion.ok else None
        score = score_case(suite, case, predicted)
        key = {"suite": suite.name, "model": label, "case_id": case.id}
        case_row = {
            **key,
            "tags": ",".join(case.tags),
            "json_valid": score.json_valid,
            "fields_correct": score.correct,
            "fields_total": score.total,
            "accuracy": score.accuracy,
            "exact_match": score.exact_match,
            "latency_s": completion.latency_s,
            "input_tokens": completion.input_tokens,
            "output_tokens": completion.output_tokens,
            "cost_usd": completion.cost_usd,
            "error": completion.error,
        }
        field_rows = [
            {
                **key,
                "field": f.path,
                "matcher": f.matcher,
                "expected": json.dumps(f.expected, ensure_ascii=False),
                "actual": json.dumps(f.actual, ensure_ascii=False),
                "correct": f.correct,
            }
            for f in score.fields
        ]
        raw = {**key, "model_id": model_id, "output": completion.text, "parsed": predicted}
        with lock:
            done += 1
            if progress:
                progress(done, len(jobs))
        return case_row, field_rows, raw

    with ThreadPoolExecutor(max_workers=max(1, config.concurrency)) as pool:
        results = list(pool.map(execute, jobs))

    case_rows = [r[0] for r in results]
    field_rows = [row for r in results for row in r[1]]
    run_id = f"{started.strftime('%Y%m%dT%H%M%SZ')}-{config.name}"
    return RunResult(
        run_id=run_id,
        config_name=config.name,
        started_at=started.isoformat(),
        cases=pd.DataFrame(case_rows),
        fields=pd.DataFrame(field_rows),
        raw=[r[2] for r in results],
    )
