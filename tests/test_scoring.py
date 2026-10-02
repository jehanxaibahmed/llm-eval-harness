import pytest

from llm_eval.dataset import FieldRule, Suite, TestCase
from llm_eval.scoring import extract_json, match, score_case


@pytest.mark.parametrize(
    "text",
    [
        '{"a": 1}',
        'Here you go:\n```json\n{"a": 1}\n```',
        'Sure! The result is {"a": 1} hope that helps',
    ],
)
def test_extract_json_variants(text):
    assert extract_json(text) == {"a": 1}


def test_extract_json_none():
    assert extract_json("no json here") is None
    assert extract_json("[1, 2]") is None


@pytest.mark.parametrize(
    "expected,actual,rule,ok",
    [
        ("ACME Ltd", "  acme   ltd ", FieldRule(), True),
        ("ACME", "ACME Inc", FieldRule(), False),
        (12.5, "12.50", FieldRule(), True),
        ("A1", "a1", FieldRule("exact"), False),
        (100.0, "£100.004", FieldRule("numeric", 0.01), True),
        (100.0, "1,234.00", FieldRule("numeric", 0.01), False),
        ("2026-03-04", "04/03/2026", FieldRule("date"), True),
        ("2026-03-04", "March 4, 2026", FieldRule("date"), True),
        ("2026-03-04", "2026-04-03", FieldRule("date"), False),
        (["a", "B"], ["b", "A"], FieldRule("unordered_list"), True),
        (["a", "a"], ["a"], FieldRule("unordered_list"), False),
        (None, None, FieldRule(), True),
        (None, "x", FieldRule(), False),
    ],
)
def test_matchers(expected, actual, rule, ok):
    assert match(expected, actual, rule) is ok


def _suite(rules=None):
    return Suite("s", "", "{input}", [], rules or {})


def test_score_case_nested_and_lists():
    case = TestCase(
        "c1",
        "",
        {
            "customer": {"name": "Acme"},
            "items": [{"sku": "A1", "qty": 2}, {"sku": "B2", "qty": 1}],
            "tags": ["x", "y"],
        },
    )
    suite = _suite({"items.sku": FieldRule("exact"), "tags": FieldRule("unordered_list")})
    predicted = {
        "customer": {"name": "ACME"},
        "items": [{"sku": "A1", "qty": "2"}],
        "tags": ["y", "x"],
    }
    score = score_case(suite, case, predicted)
    by_path = {f.path: f.correct for f in score.fields}
    assert by_path == {
        "customer.name": True,
        "items[0].sku": True,
        "items[0].qty": True,
        "items[1].sku": False,
        "items[1].qty": False,
        "tags": True,
    }
    assert score.accuracy == pytest.approx(4 / 6)
    assert not score.exact_match


def test_score_case_invalid_json():
    case = TestCase("c1", "", {"a": 1, "b": 2})
    score = score_case(_suite(), case, None)
    assert not score.json_valid
    assert score.total == 2 and score.correct == 0


def test_exact_match():
    case = TestCase("c1", "", {"a": "x"})
    assert score_case(_suite(), case, {"a": "X", "extra": 1}).exact_match
