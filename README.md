# 📏 LLM Eval Harness

![Status](https://img.shields.io/badge/status-v0.1-blue?style=for-the-badge) [![CI](https://img.shields.io/github/actions/workflow/status/jehanxaibahmed/llm-eval-harness/ci.yml?branch=main&style=for-the-badge&label=CI)](https://github.com/jehanxaibahmed/llm-eval-harness/actions/workflows/ci.yml) ![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white) ![pytest](https://img.shields.io/badge/pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white) ![OpenRouter](https://img.shields.io/badge/OpenRouter-6566F1?style=for-the-badge&logo=openai&logoColor=white) ![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)

> A lightweight harness for measuring how accurately different LLMs extract structured data, and at what cost and speed.

## 🎯 Why this project

Choosing a model for production is hard without numbers. This harness runs the same labelled test set through several models and reports field-level accuracy, cost per document and latency, so model choices are based on evidence rather than guesswork.

## 🚀 Quickstart

```bash
make install                                   # venv + editable install with dev tools
.venv/bin/llm-eval run -c configs/mock.yaml    # offline run, no API key needed
open results/*/report.html
```

Live run across real models via [OpenRouter](https://openrouter.ai):

```bash
export OPENROUTER_API_KEY=sk-or-...
.venv/bin/llm-eval run -c configs/openrouter.yaml
```

### Local models with Ollama

Any OpenAI-compatible endpoint works, including [Ollama](https://ollama.com). No real API key is needed (a dummy one is sent), and cost is reported as 0 unless you set a `price` on a model.

```bash
ollama pull llama3.1:8b
.venv/bin/llm-eval run -c configs/ollama.yaml
```

`configs/ollama.yaml` sets `provider: openai_compatible` and `base_url: http://localhost:11434/v1`. Edit its `models` list to match what you have pulled. Set `api_key_env: MY_KEY_VAR` if your server needs a real key. Avoid reasoning models such as `deepseek-r1`: their thinking output breaks JSON parsing.

| Command | What it does |
|---|---|
| `llm-eval run -c <config>` | Run every suite × model × case, save artefacts and reports |
| `llm-eval run -c <config> --check` | …and exit non-zero if metrics regress against the baseline |
| `llm-eval run -c <config> --update-baseline` | …and save this run as the new baseline |
| `llm-eval report <run_dir>` | Rebuild `report.md` / `report.html` from a saved run |
| `llm-eval check <run_dir> -b <baseline.json>` | Regression check with threshold flags |

## 📊 Sample results

Offline run of the bundled suites with three simulated models (see [`docs/sample-report/`](docs/sample-report/) for the full [Markdown](docs/sample-report/report.md) and [HTML](docs/sample-report/report.html) reports):

| Model | Field accuracy | Exact match | Valid JSON | Latency p50 | Total cost (24 docs) |
|---|---|---|---|---|---|
| precise-large | 97.5% | 58.3% | 100.0% | 2.31s | $0.0673 |
| balanced-medium | 87.5% | 20.8% | 95.8% | 1.12s | $0.00806 |
| fast-small | 63.1% | 0.0% | 91.7% | 0.38s | $0.00180 |

Each suite section also lists picks (most accurate, cheapest, fastest, best value), each model's weakest fields, and the lowest-scoring documents.

> The mock numbers come from seeded quality profiles. They show the pipeline working and are not a benchmark of real models.

## 🧱 Project layout

```
src/llm_eval/
  dataset.py          suite format + validation
  scoring/            JSON extraction, matchers, field-level scorer
  providers/          OpenRouter (live) and Mock (offline) behind one Provider protocol
  pricing.py          per-token pricing fallback
  config.py           YAML run config
  runner.py           concurrent suite × model × case execution, artefact save/load
  analysis.py         pandas summaries
  report/             Markdown + self-contained HTML comparison reports
  regression.py       baseline comparison and thresholds
  cli.py              llm-eval entry point
evals/<suite>/        suite.yaml · prompt.md · cases.jsonl
configs/              mock.yaml (CI) · openrouter.yaml (live) · ollama.yaml (local)
baselines/            committed metrics the CI gate compares against
docs/                 architecture notes and a sample report
```

See [docs/architecture.md](docs/architecture.md) for the data flow, metric definitions and design decisions.

## ➕ Adding a suite

1. Create `evals/my_suite/` with:
   - `prompt.md`: the instructions, with an `{input}` placeholder
   - `cases.jsonl`: one `{"id", "input", "expected", "tags"?}` per line
   - `suite.yaml`: name, description and per-field rules, for example:
     ```yaml
     fields:
       invoice_number: exact
       issue_date: date
       total: { matcher: numeric, tolerance: 0.01 }
       line_items.sku: exact        # applies to every list item
       tags: unordered_list
     ```
2. Add it to `suites:` in a config, then run `llm-eval run -c ... --update-baseline` if CI should gate it.

## ✅ CI

Every push and PR runs ruff and pytest on Python 3.12 and 3.13. It then runs the offline eval with `--check` against `baselines/mock.json`. The regression table and full report go to the job summary, and the results are uploaded as an artifact. A manual `workflow_dispatch` run with `live: true` also evaluates real models through OpenRouter (it needs the `OPENROUTER_API_KEY` secret).

## 🗺️ Roadmap

- [x] Labelled test-set format (input and expected JSON)
- [x] Field-level accuracy scoring
- [x] Cost and latency tracking per model
- [x] Side-by-side model comparison report
- [x] Regression checks in CI
- [x] Example evals for order and invoice extraction
- [ ] Response caching to make re-runs free
- [ ] LLM-as-judge matcher for free-text fields
- [ ] Trend charts across historical runs

## 📌 Status

v0.1: the full pipeline works end to end, offline and live. It uses synthetic sample data only.

---

Built by [Jahanzaib Ahmad](https://github.com/jehanxaibahmed) · Full Stack Engineer · AI & LLM Systems
