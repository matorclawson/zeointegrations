.PHONY: verify

# Own-lane gate under Architect's 2026-10-24 standing ruling.
# Populate the approved frozen dependency/build cache before offline verification.
verify:
	uv sync --frozen --offline --no-editable --reinstall-package zeo-integration-kit
	uv run --frozen --offline --no-sync ruff check .
	uv run --frozen --offline --no-sync ruff format --check .
	uv run --frozen --offline --no-sync python -m unittest discover -s tests -v
	uv build --offline --no-sources
