# cycl

[![PyPI](https://img.shields.io/pypi/v/cycl)](https://pypi.org/project/cycl/)
[![Downloads](https://static.pepy.tech/badge/cycl/month)](https://pepy.tech/project/cycl)
[![Build Status](https://github.com/tcm5343/cycl/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/tcm5343/cycl/actions)

cycl is a CLI and Python SDK to help identify cross-stack import/export circular dependencies, for a given AWS account and region.

### Why use cycl?

Over the lifetime of a project, circular references are bound to be introduced. They may not be noticed until you need to re-deploy some infrastructure. A good example is disaster recovery testing and potentially deploying all your infrastructure from scratch in a new region. This tool allows you to scan 

## Getting Started

The project is intended to be ran and published via a 

