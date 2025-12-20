SHELL := /bin/bash
.DEFAULT_GOAL := help
.PHONY: help install lint fmt test ci clean docs docs-serve docs-clean

help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } /^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

##@ Development

install: ## Install pv as a uv tool
	@uv tool install . --force --reinstall --python 3.14

lint: ## Run ruff linter with fixes
	@uv run ruff check src/ tests/ --fix

fmt: ## Format code with ruff
	@uv run ruff format src/ tests/

test: ## Run tests with 100% coverage requirement
	@uv run pytest

ci: lint fmt test ## Run all checks

##@ Documentation

docs: ## Build documentation
	@uv run --group docs sphinx-build -W -b html docs/ docs/_build/html

docs-serve: docs ## Build and serve documentation on random port
	@uv run --group docs python -c "import http.server,socketserver,socket,os;os.chdir('docs/_build/html');s=socket.socket();s.bind(('',0));port=s.getsockname()[1];s.close();print(f'Serving docs at http://localhost:{port}',flush=True);socketserver.TCPServer(('',port),http.server.SimpleHTTPRequestHandler).serve_forever()"

docs-clean: ## Clean documentation build
	@rm -rf docs/_build/

##@ Cleanup

clean: docs-clean ## Clean all build artifacts
	@rm -rf build/ dist/ .ruff_cache/ .venv/ .coverage htmlcov/
	@find . -name '*.pyc' -delete 2>/dev/null || true
	@find . -name '__pycache__' -delete 2>/dev/null || true
