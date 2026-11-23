SHELL := /bin/bash
.SHELLFLAGS = -ec
.PHONY: help clean lock install format test test-lower test-upper validate doc-serve build-e2e-infra destroy-e2e-infra run-e2e deploy

export CDK_DISABLE_CLI_TELEMETRY = true
export UV_NO_PROGRESS = true

BRANCH_NAME = $(shell git rev-parse --abbrev-ref HEAD)

help:
	@grep -Eh '\s##\s' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m  %-30s\033[0m %s\n", $$1, $$2}'

clean: ## clean temp files from directory
	@rm -rf .venv/ docs/_build .ruff_cache/ .pytest_cache/ .mypy_cache/ build/ dist/ src/cycl.egg-info/
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@rm -f .coverage

lock: ## update uv.lock after changing dependencies in pyproject.toml
	uv lock

install: ## install the project and all dependency groups into .venv
	uv sync --locked --all-groups

format: install ## format the project
	uv run ruff format
	uv run ruff check --fix

validate: install ## validate the projects format, lint, and types
	uv run ruff format --check
	uv run ruff check
	uv run mypy ./src/

test-lower: ## run unit tests against the lowest allowed direct dependency versions
	PYTHONPATH=./src uv run --isolated --resolution lowest-direct --group test --with-editable . pytest tests/ --cov

test-upper: ## run unit tests against the latest allowed dependency versions
	PYTHONPATH=./src uv run --isolated --upgrade --group test --with-editable . pytest tests/ --cov

test: test-lower test-upper ## run unit tests against the lowest and latest allowed dependency versions

doc-serve: install ## serve the documentation locally
	uv run sphinx-autobuild docs docs/_build

build-e2e-infra: install ## build the e2e testing infra in AWS
	./do/build-e2e-infra.sh

destroy-e2e-infra: install ## tear down the e2e testing infra in AWS
	./do/destroy-e2e-infra.sh

# the cycl under test: this source tree by default, or e.g. CYCL_SPEC=dist/cycl-1.2.3-py3-none-any.whl / cycl==1.2.3
CYCL_SPEC ?= .
run-e2e: ## run the e2e tests against the infra deployed by build-e2e-infra (needs AWS credentials, see CYCL_SPEC)
	uv run --isolated --locked --only-group e2e --with "$(CYCL_SPEC)" pytest ./e2e/tests/

deploy: ## run main.yml for the current branch, publishing a prerelease to Test PyPI and running e2e
	gh workflow run main.yml --ref $(BRANCH_NAME)
