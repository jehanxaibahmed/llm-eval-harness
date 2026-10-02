from pathlib import Path

import pytest

from llm_eval.dataset import load_suite
from llm_eval.scoring import score_case

EVALS = Path(__file__).resolve().parent.parent / "evals"


@pytest.mark.parametrize("name", ["order_extraction", "invoice_extraction"])
def test_example_suite_is_self_consistent(name):
    suite = load_suite(EVALS / name)
    assert len(suite.cases) >= 10
    for case in suite.cases:
        assert "{input}" not in suite.render_prompt(case)
        # the expected answer must score 100% against itself under the suite's rules
        assert score_case(suite, case, case.expected).exact_match, case.id
