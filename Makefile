.PHONY: install test lint fmt

install:
	python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"

test:
	.venv/bin/pytest

lint:
	.venv/bin/ruff check src tests

fmt:
	.venv/bin/ruff format src tests
