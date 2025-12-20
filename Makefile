SHELL := /bin/bash
.DEFAULT_GOAL := help
.PHONY: help lint fmt ci clean

help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n\n"} /^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

lint: ## Run ruff linter with fixes
	@uv run ruff check src/ --fix

fmt: ## Format code with ruff
	@uv run ruff format src/

ci: lint fmt ## Run all checks

clean: ## Clean build artifacts
	@rm -rf build/ dist/ .ruff_cache/ .venv/
	@find . -name '*.pyc' -delete 2>/dev/null || true
	@find . -name '__pycache__' -delete 2>/dev/null || true
