# cycl

[![PyPI](https://img.shields.io/pypi/v/cycl)](https://pypi.org/project/cycl/)
[![Downloads](https://static.pepy.tech/badge/cycl)](https://pypi.python.org/pypi/cycl/)
[![PyPI Supported Python Versions](https://img.shields.io/pypi/pyversions/cycl.svg)](https://pypi.python.org/pypi/cycl/)
[![Build Status](https://github.com/tcm5343/cycl/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/tcm5343/cycl/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

cycl is a CLI and Python SDK to help identify cross-stack import/export circular dependencies, for a given AWS account and region. The successor to [circular-dependency-detector](https://github.com/tcm5343/circular-dependency-detector), which was built at the University of Texas at Austin.

## Getting started

It is recommended to use `pipx` to install `cycl` but you can also use `pip` by simply running `pip install cycl`.

### CLI

- `cycl check --exit-zero` - exit 0 regardless of result
- `cycl check --log-level` - set the logging level (default: WARNING)
- `cycl check --cdk-out /path/to/cdk.out` - path to cdk.out, where stacks are CDK synthesized to CFN templates

## How to use cycl?

There are two main use cases for `cycl`.

1. In a pipeline. `cycl` is best used to detect circular dependencies before a deployment. If you're using the AWS CDK v2 (v1 support coming soon), simply synthesize you templates to a directory and pass that directory to `cycl` using `--cdk-out-path some-path-here`. This allows `cycl` to find all existing cycles and then those to be introduced by the deployment. This prevents the circular dependency from ever being introduced. If your pipeline deploys more than once, you should execute `cycl` before each deployment.
2. To perform analysis. While a CLI is best used in a pipeline, if you require analysis which is not currently supported, you can use the SDK. The SDK gives you all the information that `cycl` collects.

## Why use cycl?

Over the lifetime of a project, circular references are bound to be introduced. They may not be noticed until you need to re-deploy some infrastructure. A good example is disaster recovery testing and potentially deploying all your infrastructure from scratch in a new region. This tool detects those changes.

## Contributing

`cycl` is being actively developed, instructions will come as it becomes more stable.

To run specific tests:
`tox -e py39 -- ./tests/utils/cdk_test.py`
`make test ARGS=./tests/utils/cdk_test.py`
