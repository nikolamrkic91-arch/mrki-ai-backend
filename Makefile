# Mrki Makefile
# Common development tasks

.PHONY: help install install-dev test lint format typecheck coverage clean build docs serve-docs docker-build docker-run all check ci

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)Mrki Development Commands$(NC)"
	@echo "========================"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Installation
install: ## Install package
	@echo "$(BLUE)Installing Mrki...$(NC)"
	pip install -e .

install-dev: ## Install package with development dependencies
	@echo "$(BLUE)Installing Mrki with development dependencies...$(NC)"
	pip install -e ".[dev,test,docs]"
	pre-commit install

install-all: ## Install package with all optional dependencies
	@echo "$(BLUE)Installing Mrki with all dependencies...$(NC)"
	pip install -e ".[all,dev,test,docs]"

# Testing
test: ## Run tests
	@echo "$(BLUE)Running tests...$(NC)"
	pytest

test-verbose: ## Run tests with verbose output
	@echo "$(BLUE)Running tests (verbose)...$(NC)"
	pytest -v

test-coverage: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	pytest --cov=mrki --cov-report=term-missing --cov-report=html

test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(NC)"
	pytest -m unit

test-integration: ## Run integration tests only
	@echo "$(BLUE)Running integration tests...$(NC)"
	pytest -m integration

test-fast: ## Run tests in parallel (fast)
	@echo "$(BLUE)Running tests in parallel...$(NC)"
	pytest -n auto

# Code Quality
lint: ## Run linter (ruff)
	@echo "$(BLUE)Running linter...$(NC)"
	ruff check src/ tests/

lint-fix: ## Run linter and fix issues
	@echo "$(BLUE)Running linter with auto-fix...$(NC)"
	ruff check --fix src/ tests/

format: ## Format code (ruff format)
	@echo "$(BLUE)Formatting code...$(NC)"
	ruff format src/ tests/

format-check: ## Check code formatting
	@echo "$(BLUE)Checking code formatting...$(NC)"
	ruff format --check src/ tests/

typecheck: ## Run type checker (mypy)
	@echo "$(BLUE)Running type checker...$(NC)"
	mypy src/

security: ## Run security checks
	@echo "$(BLUE)Running security checks...$(NC)"
	bandit -r src/
	safety check

check: lint typecheck test ## Run all checks (lint, typecheck, test)
	@echo "$(GREEN)All checks passed!$(NC)"

ci: format-check lint typecheck test ## Run CI checks
	@echo "$(GREEN)CI checks passed!$(NC)"

# Coverage
coverage: ## Generate coverage report
	@echo "$(BLUE)Generating coverage report...$(NC)"
	pytest --cov=mrki --cov-report=html --cov-report=xml
	@echo "$(GREEN)Coverage report generated in htmlcov/$(NC)"

coverage-view: coverage ## Generate and view coverage report
	@echo "$(BLUE)Opening coverage report...$(NC)"
	python -m webbrowser htmlcov/index.html

# Documentation
docs: ## Build documentation
	@echo "$(BLUE)Building documentation...$(NC)"
	mkdocs build

serve-docs: ## Serve documentation locally
	@echo "$(BLUE)Serving documentation...$(NC)"
	mkdocs serve

deploy-docs: ## Deploy documentation to GitHub Pages
	@echo "$(BLUE)Deploying documentation...$(NC)"
	mkdocs gh-deploy

# Building
build: ## Build package
	@echo "$(BLUE)Building package...$(NC)"
	python -m build

check-dist: build ## Check distribution
	@echo "$(BLUE)Checking distribution...$(NC)"
	twine check dist/*

# Cleaning
clean: ## Clean build artifacts
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf site/

clean-all: clean ## Clean all artifacts including virtual environment
	@echo "$(BLUE)Cleaning all artifacts...$(NC)"
	rm -rf venv/
	rm -rf .venv/

# Docker
docker-build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	docker build -t mrki:latest .

docker-run: ## Run Docker container
	@echo "$(BLUE)Running Docker container...$(NC)"
	docker run -p 8080:8080 mrki:latest

docker-compose-up: ## Start services with docker-compose
	@echo "$(BLUE)Starting services...$(NC)"
	docker-compose up -d

docker-compose-down: ## Stop services with docker-compose
	@echo "$(BLUE)Stopping services...$(NC)"
	docker-compose down

docker-compose-logs: ## View docker-compose logs
	@echo "$(BLUE)Viewing logs...$(NC)"
	docker-compose logs -f

# Development Server
run: ## Run development server
	@echo "$(BLUE)Starting development server...$(NC)"
	mrki server start --debug --reload

run-prod: ## Run production server
	@echo "$(BLUE)Starting production server...$(NC)"
	mrki server start

# Database
migrate: ## Run database migrations
	@echo "$(BLUE)Running migrations...$(NC)"
	alembic upgrade head

migrate-create: ## Create new migration
	@echo "$(BLUE)Creating new migration...$(NC)"
	@read -p "Enter migration message: " message; \
	alembic revision --autogenerate -m "$$message"

db-reset: ## Reset database
	@echo "$(YELLOW)Resetting database...$(NC)"
	@read -p "Are you sure? [y/N] " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		rm -f ~/.config/mrki/mrki.db; \
		alembic upgrade head; \
		echo "$(GREEN)Database reset complete$(NC)"; \
	else \
		echo "$(YELLOW)Cancelled$(NC)"; \
	fi

# Utilities
update-deps: ## Update dependencies
	@echo "$(BLUE)Updating dependencies...$(NC)"
	pip install --upgrade -e ".[dev,test,docs]"

outdated: ## Check for outdated dependencies
	@echo "$(BLUE)Checking for outdated dependencies...$(NC)"
	pip list --outdated

license-check: ## Check licenses of dependencies
	@echo "$(BLUE)Checking licenses...$(NC)"
	pip-licenses

version: ## Show version
	@echo "$(BLUE)Mrki version:$(NC)"
	@python -c "import mrki; print(mrki.__version__)"

shell: ## Open Python shell with mrki loaded
	@echo "$(BLUE)Opening Python shell...$(NC)"
	@python -c "import mrki; print('Mrki', mrki.__version__, 'loaded'); import code; code.interact(local=locals())"

# Release
release-check: ## Check release readiness
	@echo "$(BLUE)Checking release readiness...$(NC)"
	@echo "Running all checks..."
	$(MAKE) ci
	@echo "Checking changelog..."
	@grep -q "## \[$(shell python -c 'import mrki; print(mrki.__version__)')\]" CHANGELOG.md || (echo "$(RED)Version not in CHANGELOG.md$(NC)" && exit 1)
	@echo "$(GREEN)Ready for release!$(NC)"

tag-release: ## Create git tag for release
	@echo "$(BLUE)Creating release tag...$(NC)"
	@version=$$(python -c "import mrki; print(mrki.__version__)"); \
	git tag -a "v$$version" -m "Release version $$version"; \
	echo "$(GREEN)Created tag v$$version$(NC)"; \
	echo "Run 'git push origin v$$version' to trigger release"

# All-in-one
all: clean install-dev check docs build ## Run complete build process
	@echo "$(GREEN)Complete build finished!$(NC)"

# GitHub Actions simulation
github-actions: ## Simulate GitHub Actions locally (requires act)
	@echo "$(BLUE)Running GitHub Actions locally...$(NC)"
	act push
