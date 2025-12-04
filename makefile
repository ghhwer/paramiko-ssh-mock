.PHONY: build install clean test docs install-dev

build:
	uv build

install:
	uv pip install dist/*.whl

install-dev:
	uv sync --dev

test:
	uv run pytest

clean:
	rm -rf build dist *.egg-info

docs:
	uv run mkdocs serve

docs-build:
	uv run mkdocs build
