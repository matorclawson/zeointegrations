.PHONY: setup verify qualify-inventory

setup:
	uv sync --frozen

verify:
	uv run --frozen --offline --no-sync ruff check .
	uv run --frozen --offline --no-sync ruff format --check .
	uv run --frozen --offline --no-sync python -m unittest discover -s tests -v
	git diff --check 4b825dc642cb6eb9a060e54bf8d69288fbee4904 HEAD

qualify-inventory: verify
	uv run --frozen --offline --no-sync python -m tools.qualify_inventory
