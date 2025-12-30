SHELL := /bin/bash
.SHELLFLAGS = -ec
.PHONY = clean format test validate doc-serve \
        install-test-deps install-doc-deps install-validation-deps install-e2e-deps \
        build-e2e-infra destroy-e2e-infra run-e2e

export CDK_DISABLE_CLI_TELEMETRY = true
export UV_NO_PROGRESS = true

VENV := .venv
BRANCH_NAME := $(shell git rev-parse --abbrev-ref HEAD)
REPO_NAME := $(shell basename -s .git `git config --get remote.origin.url`)
PYTHON_VERSION ?= 3.10

help:
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m  %-30s\033[0m %s\n", $$1, $$2}'

$(VENV):
	uv venv $(VENV)

lock: pyproject.toml
	uv lock

install: | $(VENV)
	uv sync --all-extras

install-test-deps: pyproject.toml uv.lock  ## install test deps
	uv sync --extra test

install-doc-deps: pyproject.toml uv.lock ## install doc deps
	uv sync --extra doc

install-validation-deps: pyproject.toml uv.lock ## install validation deps
	uv sync --extra validation

# install-e2e-deps: pyproject.toml uv.lock ## install e2e deps
# 	uv pip install --requirement ./e2e/requirements-dev.txt

format: install-test-deps ## format the project
	uv run ruff format
	uv run ruff check --fix

validate: install-validation-deps ## validate the projects format, lint, and types
	uv run ruff format --check
	uv run ruff check
	uv run mypy ./src/

test: install-test-deps ## run unit tests
	PYTHONPATH=./src uv run --isolated --with-editable '.[test]' pytest -n 0 tests/ --cov=./src/

# doc-serve: install-doc-deps ## serve the documentation locally
# 	uv run --python $(VENV)/bin/python sphinx-autobuild -M html docs docs/_build

build-e2e-infra: install-e2e-deps ## build the e2e testing infra in AWS
	@( \
		pushd e2e/infra; \
		export PYTHONPATH=.; \
		rm -rf ./cdk.out; \
		uv run cdk synth --output cdk.out; \
		uv run cdk deploy --app cdk.out CyclicStage/** --ci --require-approval never; \
		uv run cdk deploy --app cdk.out AcyclicStage/** --ci --require-approval never; \
		uv run cdk deploy --app cdk.out BootstrapE2EStack --ci --require-approval never; \
		rm -rf ./cdk.out; \
		uv run cdk synth --output cdk.out -c create_cycle=true; \
		uv run cdk deploy --app cdk.out CyclicStage/** --ci --require-approval never; \
		uv run cdk deploy --app cdk.out AcyclicStage/** --ci --require-approval never; \
		popd; \
	)

destroy-e2e-infra: install-e2e-deps ## tear down the e2e testing infra in AWS
	@( \
		pushd e2e/infra; \
		export PYTHONPATH=.; \
		rm -rf ./cdk.out; \
		uv run cdk synth --output cdk.out; \
		uv run cdk deploy --app cdk.out CyclicStage/** --ci --require-approval never; \
		uv run cdk deploy --app cdk.out AcyclicStage/** --ci --require-approval never; \
		uv run cdk destroy CyclicStage/** --ci --force; \
		uv run cdk destroy AcyclicStage/** --ci --force; \
		uv run cdk destroy BootstrapE2EStack --ci --force; \
		popd; \
	)

run-e2e: | $(VENV) ## run e2e tests in AWS, using
	uv pip install --requirement ./e2e/requirements-dev.txt
	uv run --no-project pytest ./e2e/tests/

clean: ## clean temp files from directory
	rm -rf $(VENV)
	rm -rf build dist .tox
	rm -rf docs/_build
	rm -rf .ruff_cache .pytest_cache .mypy_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
