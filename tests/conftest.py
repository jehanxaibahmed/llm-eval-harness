import json
from pathlib import Path

import pytest
import yaml


@pytest.fixture
def make_suite(tmp_path: Path):
    """Write a minimal suite to disk and return its directory."""

    def _make(cases, fields=None, prompt="Extract JSON.\n\n{input}"):
        d = tmp_path / "suite"
        d.mkdir(exist_ok=True)
        (d / "prompt.md").write_text(prompt)
        meta = {"name": "showcase", "description": "showcase suite", "fields": fields or {}}
        (d / "suite.yaml").write_text(yaml.safe_dump(meta))
        (d / "cases.jsonl").write_text("\n".join(json.dumps(c) for c in cases))
        return d

    return _make
