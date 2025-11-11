.PHONY: help install dev-install lint format test clean run

# Default target
help:
	@echo "Neural Dive - Development Commands"
	@echo "==================================="
	@echo ""
	@echo "Setup:"
	@echo "  make install       Install package dependencies"
	@echo "  make dev-install   Install package + dev dependencies"
	@echo "  make hooks         Install pre-commit hooks"
	@echo ""
	@echo "Development:"
	@echo "  make lint          Run linting checks (ruff)"
	@echo "  make format        Auto-format code (ruff)"
	@echo "  make check         Run lint + format check"
	@echo "  make test          Run tests with pytest"
	@echo "  make test-cov      Run tests with coverage report"
	@echo ""
	@echo "Running:"
	@echo "  make run           Run the game"
	@echo "  make run-classic   Run with classic theme"
	@echo "  make run-light     Run with light background"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean         Remove build artifacts and caches"

# Installation
install:
	pip install -e .

dev-install:
	pip install -e ".[dev]"

hooks:
	pre-commit install

# Linting and formatting
lint:
	ruff check neural_dive/

format:
	ruff format neural_dive/

check: lint
	ruff format --check neural_dive/

fix:
	ruff check --fix neural_dive/
	ruff format neural_dive/

# Testing
test:
	pytest neural_dive/tests/

test-cov:
	pytest neural_dive/tests/ --cov=neural_dive --cov-report=html --cov-report=term

# Running the game
run:
	python -m neural_dive

run-classic:
	python -m neural_dive --theme classic

run-light:
	python -m neural_dive --background light

run-debug:
	python -m neural_dive --fixed --seed 42

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
