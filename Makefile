.PHONY: install lint format test help

PYTHON = python3
VENV = .venv
BIN = $(VENV)/bin

help:
	@echo "Available commands:"
	@echo "  install    : Create virtual environment and install dependencies"
	@echo "  lint       : Run ruff for linting"
	@echo "  format     : Run ruff for formatting"
	@echo "  test       : Run tests using pytest"
	@echo "  pre-commit : Run pre-commit on all files"

$(VENV):
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip

install: $(VENV)
	$(BIN)/pip install -e ".[dev]"
	$(BIN)/pre-commit install

lint:
	$(BIN)/ruff check .

format:
	$(BIN)/ruff format .

test:
	$(BIN)/pytest

pre-commit:
	$(BIN)/pre-commit run --all-files
