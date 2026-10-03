import json
from unittest.mock import patch, MagicMock
import pytest
from llm_eval.pricing import ModelPrice, estimate_tokens
from llm_eval.providers import MockProfile, MockProvider, LiteLLMProvider
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

@pytest.fixture
def mock_completion():
    with patch("litellm.completion") as mock:
        yield mock

def make_completion_response(content='```json\n{"a": 1}\n```', prompt_tokens=100, completion_tokens=20):
    resp = MagicMock()
    msg = MagicMock()
    msg.content = content
    resp.choices = [MagicMock(message=msg)]
    resp.usage = MagicMock(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)
    resp.model = "gpt-4o-mini"
    return resp

def test_litellm_parses_usage_and_prices(mock_completion):
    mock_completion.return_value = make_completion_response()
    with patch("litellm.completion_cost", return_value=None):
        provider = LiteLLMProvider(api_key="k", prices={"x/y": ModelPrice(1.0, 2.0)})
        out = provider.complete("x/y", "prompt")
        
    assert out.ok
    assert extract_json(out.text) == {"a": 1}
    assert (out.input_tokens, out.output_tokens) == (100, 20)
    assert out.cost_usd == pytest.approx((100 * 1 + 20 * 2) / 1e6)

def test_litellm_prefers_reported_cost(mock_completion):
    mock_completion.return_value = make_completion_response()
    with patch("litellm.completion_cost", return_value=0.0123):
        provider = LiteLLMProvider(api_key="k")
        out = provider.complete("x/y", "p")
    assert out.cost_usd == pytest.approx(0.0123)

def test_litellm_handles_error(mock_completion):
    mock_completion.side_effect = Exception("bad key")
    out = LiteLLMProvider(api_key="k").complete("x/y", "p")
    assert not out.ok and "bad key" in out.error

