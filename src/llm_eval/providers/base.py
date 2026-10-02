from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Completion:
    text: str
    input_tokens: int
    output_tokens: int
    latency_s: float
    cost_usd: float
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


class Provider(Protocol):
    def complete(self, model: str, prompt: str) -> Completion: ...
