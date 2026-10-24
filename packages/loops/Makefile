.PHONY: verify

# Invoke only in Runtime's permitted Python venue with the complete offline
# lock/tool/build closure. A source checkout or existing cache is not admission.
verify:
	uv sync --frozen --offline --no-editable
	uv run --frozen --offline --no-sync ruff check .
	uv run --frozen --offline --no-sync ruff format --check .
	uv run --frozen --offline --no-sync python -m unittest discover -s tests -v
	uv build --offline --no-sources
