.PHONY: verify

verify:
	uv sync --frozen --offline --no-editable --reinstall-package zeo-integration-hubspot
	uv run --frozen --offline --no-sync ruff check .
	uv run --frozen --offline --no-sync ruff format --check .
	uv run --frozen --offline --no-sync python -m unittest discover -s tests -v
	uv build --offline --no-sources
