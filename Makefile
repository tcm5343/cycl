help:
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m  %-30s\033[0m %s\n", $$1, $$2}'

format:  ## format the project
	ruff format
	ruff check --fix

test:  ## run unit tests and generate coverage report
	pytest --cov=./src/ ./tests/
