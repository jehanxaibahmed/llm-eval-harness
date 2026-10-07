import time
from typing import Any

import litellm

from llm_eval.pricing import ModelPrice
from llm_eval.providers.base import Completion


class LiteLLMProvider:
    def __init__(
        self,
        api_key: str | None = None,
        prices: dict[str, ModelPrice] | None = None,
        timeout_s: float = 60.0,
        max_retries: int = 3,
        temperature: float = 0.0,
        base_url: str | None = None,
        **kwargs: Any,
    ) -> None:
        self.api_key = api_key
        self.prices = prices or {}
        self.timeout_s = timeout_s
        self.max_retries = max_retries
        self.temperature = temperature
        self.base_url = base_url

    def complete(self, model: str, prompt: str) -> Completion:
        messages = [
            {
                "role": "system",
                "content": (
                    "You extract structured data. Reply with a single JSON object and nothing else."
                ),
            },
            {"role": "user", "content": prompt},
        ]

        kwargs: dict[str, Any] = {}
        if self.api_key:
            kwargs["api_key"] = self.api_key
        if self.base_url:
            kwargs["api_base"] = self.base_url

        start = time.perf_counter()
        last_error = "unknown error"

        try:
            resp = litellm.completion(
                model=model,
                messages=messages,
                temperature=self.temperature,
                timeout=self.timeout_s,
                num_retries=self.max_retries,
                **kwargs,
            )
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            return Completion("", 0, 0, time.perf_counter() - start, 0.0, error=last_error)

        latency_s = time.perf_counter() - start

        if not resp.choices:
            return Completion("", 0, 0, latency_s, 0.0, error="No choices returned")

        text = resp.choices[0].message.content or ""

        usage = resp.usage
        in_tok = usage.prompt_tokens if usage else 0
        out_tok = usage.completion_tokens if usage else 0

        # litellm calculates cost, let's try to get it
        cost = litellm.completion_cost(completion_response=resp)
        if cost is None:
            price = self.prices.get(model)
            cost = price.cost(in_tok, out_tok) if price else 0.0

        return Completion(text, in_tok, out_tok, latency_s, float(cost))
