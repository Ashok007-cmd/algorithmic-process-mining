.PHONY: install install-dev test test-cov lint format typecheck run-app run-notebook clean setup-graphviz

install:
	pip install -e "."

install-dev:
	pip install -e ".[dev]"

test:
	python -m pytest tests/ -v --tb=short

test-cov:
	python -m pytest tests/ -v --tb=short --cov=src --cov-report=term-missing

lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/

typecheck:
	mypy src/

run-app:
	streamlit run src/viz/dashboard.py

run-notebook:
	jupyter notebook notebooks/

setup-graphviz:
	sudo apt-get install -y graphviz graphviz-dev

clean:
	rm -rf data/raw/ data/processed/ data/models/ data/results/ .pytest_cache/ .ruff_cache/ .mypy_cache/ .pm4py_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ipynb_checkpoints -exec rm -rf {} + 2>/dev/null || true
