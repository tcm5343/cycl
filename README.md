# cycl

[![PyPI](https://img.shields.io/pypi/v/cycl)](https://pypi.org/project/cycl/)
[![Downloads](https://static.pepy.tech/badge/cycl)](https://pypi.python.org/pypi/cycl/)
[![PyPI Supported Python Versions](https://img.shields.io/pypi/pyversions/cycl.svg)](https://pypi.python.org/pypi/cycl/)
[![Build Status](https://github.com/tcm5343/cycl/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/tcm5343/cycl/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v0.json)](https://github.com/charliermarsh/ruff)
![Checked with mypy](https://img.shields.io/badge/mypy-checked-blue)

cycl is a CLI and Python SDK to help identify cross-stack import/export circular dependencies, for a given AWS account and region. The successor to [circular-dependency-detector](https://github.com/tcm5343/circular-dependency-detector), which was built at the University of Texas at Austin.

## Documentation

Documentation for using `cycl` is found [here](https://tcm5343.github.io/cycl/).

## Contributing

`cycl` is being actively developed, instructions will come as it becomes more stable.

Run `make` to see the available targets and their descriptions.

To serve the documentation pages locally, you can simply run `make docs-serve`. The address should be served on `http://0.0.0.0:8000`, if not, you can run `docker compose logs sphinx | grep "Serving"` to determine the correct address.

To run specific tests:

* `tox -e py39 -- ./tests/utils/cdk_test.py`
* `make test ARGS=./tests/utils/cdk_test.py`
