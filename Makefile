SHELL := /bin/bash
.SHELLFLAGS = -ec
.DEFAULT_GOAL = help
.PHONY = help clean format test install-deps

REQ_FILES := requirements.txt requirements-dev.txt
REQ_HASH := requirements.hash

help:
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m  %-30s\033[0m %s\n", $$1, $$2}'

# Generate a hash file based on the last modified times of REQ_FILES
# HANDLE IF ERROR TO CLEAN REQ_HASH
$(REQ_HASH): $(REQ_FILES)
	@echo "Checking if dependencies need to be installed..."
	stat -c %Y $(REQ_FILES) | md5sum | awk '{print $$1}' > $(REQ_HASH)
	@echo "Installing dependencies..."
	python3 -m venv ./.venv
	pip install -e .[dev]

install-deps: $(REQ_HASH)  ## Install dependencies if requirements files changed

format:  ## Format the project
	ruff format
	ruff check --fix

validate:  ## Validate the project is linted and formatted
	ruff format --check
	ruff check

test:  ## Run unit tests and generate coverage report
	pytest --cov=./src/ ./tests/

clean:  ## Clean generated project files
	rm -f $(REQ_HASH)
	rm -f .coverage
	rm -rf ./.ruff_cache
	rm -rf ./.pytest_cache
	# rm -rf ./.venv
	find . -type d -name "__pycache__" -exec rm -r {} +
