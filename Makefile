.PHONY: setup verify

setup:
	uv sync --frozen

verify:
	uv run --frozen ruff check .
	uv run --frozen ruff format --check .
	uv run --frozen python -m unittest discover -s tests -v
	git diff --check 4b825dc642cb6eb9a060e54bf8d69288fbee4904 HEAD
