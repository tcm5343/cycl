SHELL := /bin/bash
.SHELLFLAGS = -ec
.DEFAULT_GOAL = help
.PHONY = help clean format test install-deps venv

DEV_DEPS_CACHE := .venv/dev-deps.cache
DOCS_DEPS_CACHE := .venv/docs-deps.cache

help:
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m  %-30s\033[0m %s\n", $$1, $$2}'

$(DEV_DEPS_CACHE): pyproject.toml
	@echo "Installing development dependencies..."
	@test -d .venv || python3 -m venv .venv
	@( \
		source ./.venv/bin/activate; \
		pip install --editable .[dev]; \
		touch $(DEV_DEPS_CACHE); \
	)

install-dev-deps: $(DEV_DEPS_CACHE)  ## Install development dependencies
	@echo "Development deps have been installed..."

$(DOCS_DEPS_CACHE): pyproject.toml
	@echo "Installing documenation dependencies..."
	@test -d .venv || python3 -m venv .venv
	@( \
		source ./.venv/bin/activate; \
		pip install --editable .[doc]; \
		touch $(DOCS_DEPS_CACHE); \
	)

install-doc-deps: $(DOCS_DEPS_CACHE)  ## Install documentation dependencies
	@echo "Documentation deps have been installed..."

format: install-dev-deps  ## Format the project
	@( \
		source ./.venv/bin/activate; \
		ruff format; \
		ruff check --fix; \
	)

validate: install-dev-deps  ## Validate the projects formatting
	@( \
		source ./.venv/bin/activate; \
		ruff format --check; \
		ruff check; \
		python3 -m mypy ./src/; \
	)

test: install-dev-deps  ## Run unit tests
	@( \
		source ./.venv/bin/activate; \
		export PYTHONPATH=./src/; \
		pytest --cov=./src/ $(ARGS); \
	)
	
doc-serve: install-doc-deps ## Serve the documentation locally
	@( \
		source ./.venv/bin/activate; \
		sphinx-autobuild -M html docs docs/_build; \
	)

clean:  ## Clean generated project files
	@rm -f .coverage
	@rm -rf ./.ruff_cache
	@rm -rf ./.pytest_cache
	@rm -rf ./.venv
	@rm -rf ./.venv
	@rm -rf ./.tox
	@rm -rf ./dist
	@rm -rf ./.mypy_cache
	@rm -rf ./docs/_build
	@find . -type d -name "__pycache__" -exec rm -rf {} +
