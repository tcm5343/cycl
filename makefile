SHELL := /bin/bash
.SHELLFLAGS = -ec
.DEFAULT_GOAL = help
.PHONY = help clean format test format validate doc-serve install-test-deps install-doc-deps install-validation-deps build-e2e-infra destroy-e2e-infra

export CDK_DISABLE_CLI_TELEMETRY = true
export PIP_DISABLE_PIP_VERSION_CHECK = true

TEST_DEPS_CACHE := .venv/test-deps.cache
DOC_DEPS_CACHE := .venv/docs-deps.cache
VALIDATION_DEPS_CACHE := .venv/validation-deps.cache
E2E_DEPS_CACHE := .venv/e2e-deps.cache

BRANCH_NAME := $(shell git rev-parse --abbrev-ref HEAD)
REPO_NAME := $(shell basename -s .git `git config --get remote.origin.url`)

help:
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m  %-30s\033[0m %s\n", $$1, $$2}'

$(TEST_DEPS_CACHE): pyproject.toml
	@echo "Installing development dependencies..."
	@test -d .venv || python3 -m venv .venv
	@( \
		source ./.venv/bin/activate; \
		pip install --editable .[test]; \
		touch $(TEST_DEPS_CACHE); \
	)

install-test-deps: $(TEST_DEPS_CACHE)  ## Install development dependencies
	@echo "Development dependencies have been installed..."

$(DOC_DEPS_CACHE): pyproject.toml
	@echo "Installing documentation dependencies..."
	@test -d .venv || python3 -m venv .venv
	@( \
		source ./.venv/bin/activate; \
		pip install --editable .[doc]; \
		touch $(DOC_DEPS_CACHE); \
	)

install-doc-deps: $(DOC_DEPS_CACHE)  ## Install documentation dependencies
	@echo "Documentation dependencies have been installed..."

$(VALIDATION_DEPS_CACHE): pyproject.toml
	@echo "Installing validation dependencies..."
	@test -d .venv || python3 -m venv .venv
	@( \
		source ./.venv/bin/activate; \
		pip install --editable .[validation]; \
		touch $(VALIDATION_DEPS_CACHE); \
	)

install-validation-deps: $(VALIDATION_DEPS_CACHE)  ## Install validation dependencies
	@echo "Validation deps have been installed..."

$(E2E_DEPS_CACHE): pyproject.toml
	@echo "Installing end to end testing dependencies..."
	@test -d .venv || python3 -m venv .venv
	@( \
		source ./.venv/bin/activate; \
		pip install --editable .[e2e]; \
		touch $(E2E_DEPS_CACHE); \
	)

install-e2e-deps: $(E2E_DEPS_CACHE)  ## Install end to end testing dependencies
	@echo "End to end testing dependencies have been installed..."

format: install-test-deps  ## Format the project
	@( \
		source ./.venv/bin/activate; \
		ruff format; \
		ruff check --fix; \
	)

validate: install-validation-deps  ## Run the code quality checks
	@( \
		source ./.venv/bin/activate; \
		ruff format --check; \
		ruff check; \
		python3 -m mypy ./src/; \
	)

test: install-test-deps  ## Run unit tests
# run specific tests: make test 'ARGS=--no-cov ./tests/models'
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
	@rm -rf ./build
	@rm -rf ./.tox
	@rm -rf ./dist
	@rm -rf ./.mypy_cache
	@rm -rf ./docs/_build
	@find . -type d -name "__pycache__" -exec rm -rf {} +

build-e2e-infra: install-e2e-deps  ## Deploy the infrastructure needed for E2E testing in AWS
	@( \
		source ./.venv/bin/activate; \
		pushd e2e/infra; \
		export PYTHONPATH=.; \
		\
		rm -rf ./cdk.out; \
		cdk synth --output cdk.out; \
		cdk deploy --app cdk.out CyclicStage/** --ci --require-approval never; \
		cdk deploy --app cdk.out AcyclicStage/** --ci --require-approval never; \
		cdk deploy --app cdk.out BootstrapE2EStack --ci --require-approval never; \
		\
		rm -rf ./cdk.out; \
		cdk synth --output cdk.out -c create_cycle=true; \
		cdk deploy --app cdk.out CyclicStage/** --ci --require-approval never; \
		cdk deploy --app cdk.out AcyclicStage/** --ci --require-approval never; \
	)

destroy-e2e-infra: install-e2e-deps  ## Destroy the infrastructure for E2E testing in AWS, removing cycles and then stacks
	@( \
		source ./.venv/bin/activate; \
		pushd e2e; \
		\
		rm -rf ./cdk.out; \
		cdk synth --output cdk.out; \
		cdk deploy --app cdk.out CyclicStage/** --ci --require-approval never; \
		cdk deploy --app cdk.out AcyclicStage/** --ci --require-approval never; \
		cdk deploy --app cdk.out BootstrapE2EStack --ci --require-approval never; \
		\
		cdk destroy CyclicStage/** --ci --force; \
		cdk destroy AcyclicStage/** --ci --force; \
	)

run-e2e: install-e2e-deps  ## Run E2E tests
	@( \
		source ./.venv/bin/activate; \
		pushd e2e; \
		\
		pytest ./tests/; \
	)
