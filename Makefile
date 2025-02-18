SHELL := /bin/bash
.SHELLFLAGS = -ec
.DEFAULT_GOAL = help
.PHONY = help clean format test install-deps

REQ_FILES := requirements.txt requirements-dev.txt
REQ_CACHE := requirements.cache

help:
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m  %-30s\033[0m %s\n", $$1, $$2}'

$(REQ_CACHE): $(REQ_FILES)
	@echo "Installing dependencies..."
	pip install --editable . -r requirements-dev.txt
	touch requirements.cache

install-deps: $(REQ_CACHE)  ## Install dependencies, if needed
	@echo "Dependencies have been installed..."

format:  ## Format the project
	ruff format
	ruff check --fix

validate:  ## Validate the project is linted and formatted
	ruff format --check
	ruff check
	python3 -m mypy ./src/

test:  ## Run unit tests and generate coverage report
	pytest --cov=./src/ $(ARGS)

docs-serve:  ## Serve live version of the documentation
	docker compose up sphinx --remove-orphans

clean:  ## Clean generated project files
	rm -f $(REQ_CACHE)
	rm -f .coverage
	rm -rf ./.ruff_cache
	rm -rf ./.pytest_cache
	rm -rf ./.venv
	rm -rf ./.tox
	rm -rf ./dist
	rm -rf ./.mypy_cache
	rm -rf ./docs/_build
	find . -type d -name "__pycache__" -exec rm -rf {} +
