SHELL := /bin/bash
.SHELLFLAGS = -ec
.PHONY: clean format test test-lower test-upper validate doc-serve install build-e2e-infra destroy-e2e-infra run-e2e

export CDK_DISABLE_CLI_TELEMETRY = true
export UV_NO_PROGRESS = true

BRANCH_NAME := $(shell git rev-parse --abbrev-ref HEAD)
REPO_NAME := $(shell basename -s .git `git config --get remote.origin.url`)
UV_VERSION ?= $(shell cat .python-version | grep -v "^#")

help:
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m  %-30s\033[0m %s\n", $$1, $$2}'

clean: ## clean temp files from directory
	@rm -rf .venv/ docs/_build .ruff_cache/ .pytest_cache/ .mypy_cache/ build/ dist/ src/cycl.egg-info/
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@rm -f .coverage

lock: pyproject.toml
	uv lock

install:
	uv sync --locked --all-groups

format: install ## format the project
	uv run ruff format
	uv run ruff check --fix

validate: install ## validate the projects format, lint, and types
	uv run ruff format --check
	uv run ruff check
	uv run mypy ./src/

PYTEST_CMD = pytest -n 0 tests/ --cov=./src/

test-lower: ## run unit tests against the lowest allowed direct dependency versions
	PYTHONPATH=./src uv run --isolated --resolution lowest-direct --group test --with-editable . $(PYTEST_CMD)

test-upper: ## run unit tests against the latest allowed dependency versions
	PYTHONPATH=./src uv run --isolated --upgrade --group test --with-editable . $(PYTEST_CMD)

test: test-lower test-upper ## run unit tests against the lowest and latest allowed dependency versions

doc-serve: install ## serve the documentation locally
	uv run sphinx-autobuild docs docs/_build

build-e2e-infra: install ## build the e2e testing infra in AWS
	./do/build-e2e-infra.sh

destroy-e2e-infra: install ## tear down the e2e testing infra in AWS
	./do/destroy-e2e-infra.sh

run-e2e: ## run e2e tests in AWS, using
	uv pip install --requirement ./e2e/requirements-dev.txt
	uv run --no-project pytest ./e2e/tests/
