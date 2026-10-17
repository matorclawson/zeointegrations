.PHONY: setup verify

setup:
	uv sync --frozen

verify:
	uv run --frozen ruff check .
	uv run --frozen ruff format --check .
	uv run --frozen python -m unittest discover -s tests -v
	git diff --check
