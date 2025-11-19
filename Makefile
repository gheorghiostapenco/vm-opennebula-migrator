# Makefile for VM Migrator

# Variables
VENV_NAME = venv
PYTHON = $(VENV_NAME)/bin/python
PIP = $(VENV_NAME)/bin/pip

# Colors for nice output
GREEN = \033[0;32m
NC = \033[0m # No Color

.PHONY: help install run test clean lint

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'

install: ## Create venv and install dependencies
	@echo "$(GREEN)Creating virtual environment...$(NC)"
	python3 -m venv $(VENV_NAME)
	@echo "$(GREEN)Installing dependencies...$(NC)"
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)Setup complete! Run 'source $(VENV_NAME)/bin/activate' to start.$(NC)"

run: ## Run the main application (Help)
	$(PYTHON) src/main.py --help

test: ## Run unit tests
	$(PYTHON) -m pytest tests/ -v

lint: ## Format code with Black and check with Flake8
	$(PYTHON) -m black src/ tests/
	$(PYTHON) -m flake8 src/ tests/

clean: ## Remove virtual environment and cache
	rm -rf $(VENV_NAME)
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +