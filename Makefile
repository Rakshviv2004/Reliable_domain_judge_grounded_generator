
.PHONY: install test lint format typecheck clean ingest

install:
	pip install -r requirements-dev.txt

test:
	pytest tests/ -v

lint:
	ruff check .

format:
	ruff format .

typecheck:
	mypy ingestion

ingest:
	python scripts/ingest_corpus.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
