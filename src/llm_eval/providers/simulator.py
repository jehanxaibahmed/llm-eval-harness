"""Deterministic offline provider.

It knows the expected answer for every prompt (an "oracle") and degrades it according to a
per-model profile, so the full pipeline, including reports and CI regression checks, runs
without network access or API keys.
"""

from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass
from typing import Any

from llm_eval.pricing import ModelPrice, estimate_tokens
from llm_eval.providers.base import Completion


@dataclass(frozen=True)
class simulatorProfile:
    field_error_rate: float = 0.0
    invalid_json_rate: float = 0.0
    latency_s: float = 0.5
    price: ModelPrice = ModelPrice(0.0, 0.0)
    wrap_in_prose: bool = False


DEFAULT_PROFILES: dict[str, simulatorProfile] = {
    "simulator/precise-large": simulatorProfile(0.02, 0.0, 2.4, ModelPrice(3.0, 15.0)),
    "simulator/balanced-medium": simulatorProfile(
        0.08, 0.02, 1.1, ModelPrice(0.5, 1.5), wrap_in_prose=True
    ),
    "simulator/fast-small": simulatorProfile(
        0.20, 0.06, 0.4, ModelPrice(0.1, 0.4), wrap_in_prose=True
    ),
}


class simulatorProvider:
    def __init__(
        self,
        oracle: dict[str, dict[str, Any]],
        profiles: dict[str, simulatorProfile] | None = None,
        seed: int = 0,
    ) -> None:
        self.oracle = oracle
        self.profiles = profiles or DEFAULT_PROFILES
        self.seed = seed

    def complete(self, model: str, prompt: str) -> Completion:
        profile = self.profiles.get(model)
        if profile is None:
            return Completion("", 0, 0, 0.0, 0.0, error=f"unknown simulator model {model!r}")
        rng = random.Random(self._seed_for(model, prompt))
        expected = self.oracle.get(prompt)
        if expected is None:
            text = "{}"
        elif rng.random() < profile.invalid_json_rate:
            text = "I could not find all the fields, sorry."
        else:
            answer = _corrupt(expected, profile.field_error_rate, rng)
            text = json.dumps(answer, indent=2)
            if profile.wrap_in_prose:
                text = f"Here is the extracted data:\n```json\n{text}\n```"
        in_tok, out_tok = estimate_tokens(prompt), estimate_tokens(text)
        latency = profile.latency_s * rng.uniform(0.8, 1.25)
        return Completion(text, in_tok, out_tok, latency, profile.price.cost(in_tok, out_tok))

    def _seed_for(self, model: str, prompt: str) -> int:
        digest = hashlib.sha256(f"{self.seed}|{model}|{prompt}".encode()).hexdigest()
        return int(digest[:16], 16)


def _corrupt(value: Any, rate: float, rng: random.Random) -> Any:
    if isinstance(value, dict):
        out = {}
        for key, child in value.items():
            if not isinstance(child, dict | list) and rng.random() < rate / 3:
                continue  # drop the field
            out[key] = _corrupt(child, rate, rng)
        return out
    if isinstance(value, list):
        return [_corrupt(v, rate, rng) for v in value]
    if rng.random() >= rate:
        return value
    if isinstance(value, bool):
        return not value
    if isinstance(value, int | float):
        return round(value * rng.choice([0.9, 1.1, 10]), 2)
    if isinstance(value, str) and value:
        return value[: max(1, len(value) - 2)] + "??"
    return "unknown"
