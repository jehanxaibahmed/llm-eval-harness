"""Token pricing used to compute cost per call when the provider doesn't report it."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelPrice:
    """USD per million tokens."""

    input_per_mtok: float
    output_per_mtok: float

    def cost(self, input_tokens: int, output_tokens: int) -> float:
        return (
            input_tokens * self.input_per_mtok + output_tokens * self.output_per_mtok
        ) / 1_000_000


def estimate_tokens(text: str) -> int:
    """Rough token estimate (~4 characters per token) for providers without usage data."""
    return max(1, round(len(text) / 4))
