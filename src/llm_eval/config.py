"""Run configuration loaded from YAML."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from llm_eval.pricing import ModelPrice

PROVIDERS = {"mock", "openrouter", "openai_compatible"}


@dataclass(frozen=True)
class ModelSpec:
    id: str
    label: str
    price: ModelPrice | None = None


@dataclass
class RunConfig:
    name: str
    provider: str
    suites: list[Path]
    models: list[ModelSpec]
    concurrency: int = 4
    output_dir: Path = Path("results")
    seed: int = 0
    regression: dict = field(default_factory=dict)
    base_url: str | None = None
    api_key_env: str | None = None

    @property
    def prices(self) -> dict[str, ModelPrice]:
        return {m.id: m.price for m in self.models if m.price}


def load_config(path: str | Path) -> RunConfig:
    path = Path(path)
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    base = path.parent.parent if path.parent.name == "configs" else path.parent

    provider = raw.get("provider", "mock")
    if provider not in PROVIDERS:
        raise ValueError(f"{path}: provider must be one of {sorted(PROVIDERS)}")
    if not raw.get("models"):
        raise ValueError(f"{path}: at least one model is required")
    if not raw.get("suites"):
        raise ValueError(f"{path}: at least one suite is required")

    base_url = raw.get("base_url")
    if provider == "openai_compatible" and not base_url:
        raise ValueError(f"{path}: base_url is required for provider openai_compatible")

    models = []
    for entry in raw["models"]:
        entry = {"id": entry} if isinstance(entry, str) else entry
        price = entry.get("price")
        models.append(
            ModelSpec(
                id=entry["id"],
                label=entry.get("label", entry["id"]),
                price=ModelPrice(**price) if price else None,
            )
        )

    regression = dict(raw.get("regression") or {})
    if regression.get("baseline"):
        regression["baseline"] = str((base / regression["baseline"]).resolve())

    return RunConfig(
        name=raw.get("name", path.stem),
        provider=provider,
        suites=[(base / s).resolve() for s in raw["suites"]],
        models=models,
        concurrency=int(raw.get("concurrency", 4)),
        output_dir=(base / raw.get("output_dir", "results")).resolve(),
        seed=int(raw.get("seed", 0)),
        regression=regression,
        base_url=base_url,
        api_key_env=raw.get("api_key_env"),
    )
