"""OpenRouter chat-completions client with retries, usage and cost capture."""

from __future__ import annotations

import os
import time

import httpx

from llm_eval.pricing import ModelPrice
from llm_eval.providers.base import Completion

DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
API_URL = f"{DEFAULT_BASE_URL}/chat/completions"
DEFAULT_API_KEY_ENV = "OPENROUTER_API_KEY"
LOCAL_DUMMY_KEY = "not-needed"
RETRY_STATUS = {408, 429, 500, 502, 503, 504}
SYSTEM_PROMPT = "You extract structured data. Reply with a single JSON object and nothing else."


class OpenRouterProvider:
    def __init__(
        self,
        api_key: str | None = None,
        prices: dict[str, ModelPrice] | None = None,
        timeout_s: float = 60.0,
        max_retries: int = 3,
        temperature: float = 0.0,
        client: httpx.Client | None = None,
        base_url: str | None = None,
        api_key_env: str | None = None,
        require_key: bool | None = None,
    ) -> None:
        """Chat-completions client for OpenRouter or any OpenAI-compatible endpoint.

        With no ``base_url`` this targets OpenRouter and requires a key. With a custom
        ``base_url`` (e.g. Ollama at http://localhost:11434/v1) the key is optional: it is
        read from ``api_key_env`` if that is set, otherwise a dummy value is sent.
        """
        self.base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self.is_openrouter = base_url is None
        self.url = f"{self.base_url}/chat/completions"
        env_name = api_key_env or (DEFAULT_API_KEY_ENV if self.is_openrouter else None)
        if require_key is None:
            require_key = self.is_openrouter or bool(api_key_env)
        self.api_key = api_key or (os.environ.get(env_name) if env_name else None)
        if not self.api_key:
            if require_key:
                raise RuntimeError(f"{env_name or DEFAULT_API_KEY_ENV} is not set")
            self.api_key = LOCAL_DUMMY_KEY
        self.prices = prices or {}
        self.max_retries = max_retries
        self.temperature = temperature
        self.client = client or httpx.Client(timeout=timeout_s)

    def complete(self, model: str, prompt: str) -> Completion:
        payload = {
            "model": model,
            "temperature": self.temperature,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        if self.is_openrouter:
            payload["usage"] = {"include": True}
            headers["X-Title"] = "llm-eval-harness"
        start = time.perf_counter()
        last_error = "unknown error"
        for attempt in range(self.max_retries + 1):
            try:
                resp = self.client.post(self.url, json=payload, headers=headers)
            except httpx.HTTPError as exc:
                last_error = f"{type(exc).__name__}: {exc}"
            else:
                if resp.status_code == 200:
                    return self._parse(model, resp.json(), time.perf_counter() - start)
                last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
                if resp.status_code not in RETRY_STATUS:
                    break
            if attempt < self.max_retries:
                time.sleep(min(2**attempt, 8))
        return Completion("", 0, 0, time.perf_counter() - start, 0.0, error=last_error)

    def _parse(self, model: str, body: dict, latency_s: float) -> Completion:
        if "error" in body:
            return Completion("", 0, 0, latency_s, 0.0, error=str(body["error"]))
        text = body["choices"][0]["message"].get("content") or ""
        usage = body.get("usage") or {}
        in_tok = int(usage.get("prompt_tokens", 0))
        out_tok = int(usage.get("completion_tokens", 0))
        cost = usage.get("cost")
        if cost is None:
            price = self.prices.get(model)
            cost = price.cost(in_tok, out_tok) if price else 0.0
        return Completion(text, in_tok, out_tok, latency_s, float(cost))
