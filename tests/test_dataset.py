import pytest

from llm_eval.dataset import DatasetError, FieldRule, load_suite

CASE = {"id": "c1", "input": "Order 42", "expected": {"order_id": "42"}}


def test_load_suite_roundtrip(make_suite):
    fields = {"total": {"matcher": "numeric", "tolerance": 0.01}}
    suite = load_suite(make_suite([CASE], fields=fields))
    assert suite.name == "demo"
    assert suite.cases[0].expected == {"order_id": "42"}
    assert suite.rule_for("total") == FieldRule("numeric", 0.01)
    assert suite.render_prompt(suite.cases[0]).endswith("Order 42")


def test_shorthand_rule_and_list_paths(make_suite):
    suite = load_suite(make_suite([CASE], fields={"items.sku": "exact"}))
    assert suite.rule_for("items[3].sku").matcher == "exact"
    assert suite.rule_for("unknown").matcher == "normalized"


def test_duplicate_ids_rejected(make_suite):
    with pytest.raises(DatasetError, match="duplicate"):
        load_suite(make_suite([CASE, CASE]))


def test_missing_key_rejected(make_suite):
    with pytest.raises(DatasetError, match="expected"):
        load_suite(make_suite([{"id": "x", "input": "y"}]))


def test_prompt_needs_placeholder(make_suite):
    with pytest.raises(DatasetError, match="placeholder"):
        load_suite(make_suite([CASE], prompt="no placeholder"))


def test_unknown_matcher_rejected(make_suite):
    with pytest.raises(DatasetError, match="unknown matcher"):
        load_suite(make_suite([CASE], fields={"x": "fuzzy"}))
