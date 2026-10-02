import json

import httpx
import pytest

from llm_eval.pricing import ModelPrice, estimate_tokens
from llm_eval.providers import MockProfile, MockProvider, OpenRouterProvider
from llm_eval.providers import openrouter as openrouter_mod
from llm_eval.scoring import extract_json


def test_model_price_cost():
    assert ModelPrice(3.0, 15.0).cost(1_000_000, 100_000) == pytest.approx(4.5)
    assert estimate_tokens("abcd" * 10) == 10


def test_mock_perfect_profile_returns_oracle():
    oracle = {"p1": {"a": 1, "b": {"c": "x"}}}
    provider = MockProvider(oracle, {"m": MockProfile(price=ModelPrice(1, 1))})
    out = provider.complete("m", "p1")
    assert out.ok and json.loads(out.text) == oracle["p1"]
    assert out.cost_usd > 0 and out.latency_s > 0


def test_mock_is_deterministic():
    oracle = {"p": {"a": "hello", "n": 5}}
    provider = MockProvider(oracle, {"m": MockProfile(field_error_rate=0.5)})
    assert provider.complete("m", "p") == provider.complete("m", "p")


def test_mock_unknown_model():
    assert not MockProvider({}).complete("nope", "p").ok


def _transport(responses):
    calls = iter(responses)

    def handler(request: httpx.Request) -> httpx.Response:
        status, body = next(calls)
        return httpx.Response(status, json=body)

    return httpx.MockTransport(handler)


OK_BODY = {
    "choices": [{"message": {"content": '```json\n{"a": 1}\n```'}}],
    "usage": {"prompt_tokens": 100, "completion_tokens": 20},
}


def test_openrouter_parses_usage_and_prices(monkeypatch):
    monkeypatch.setattr(openrouter_mod.time, "sleep", lambda _: None)
    client = httpx.Client(transport=_transport([(429, {}), (200, OK_BODY)]))
    provider = OpenRouterProvider(api_key="k", prices={"x/y": ModelPrice(1.0, 2.0)}, client=client)
    out = provider.complete("x/y", "prompt")
    assert out.ok
    assert extract_json(out.text) == {"a": 1}
    assert (out.input_tokens, out.output_tokens) == (100, 20)
    assert out.cost_usd == pytest.approx((100 * 1 + 20 * 2) / 1e6)


def test_openrouter_prefers_reported_cost():
    body = {**OK_BODY, "usage": {**OK_BODY["usage"], "cost": 0.0123}}
    client = httpx.Client(transport=_transport([(200, body)]))
    out = OpenRouterProvider(api_key="k", client=client).complete("x/y", "p")
    assert out.cost_usd == pytest.approx(0.0123)


def test_openrouter_non_retryable_error():
    client = httpx.Client(transport=_transport([(401, {"error": "bad key"})]))
    out = OpenRouterProvider(api_key="k", client=client).complete("x/y", "p")
    assert not out.ok and "401" in out.error


def test_openrouter_requires_key(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        OpenRouterProvider()
