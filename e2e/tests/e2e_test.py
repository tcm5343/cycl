import subprocess
import sys
import ast
import os

import pytest

from cycl.utils.testing import is_circular_reversible_permutation


def test_cyclic_region(monkeypatch):
    region = 'us-west-2'
    expected_return_code = 1
    expected_nodes_in_cycle = ['cyclic-stack-b', 'cyclic-stack-a']

    monkeypatch.setenv("AWS_DEFAULT_REGION", region)
    expected_prefix = 'cycle found between nodes: '
    env = os.environ.copy()

    result = subprocess.run(
        [
            sys.executable, "-m", "cycl", "check"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )

    assert result.returncode == expected_return_code, f"Non-zero exit: {result.returncode}\nStderr: {result.stderr}"
    assert result.stdout.startswith(expected_prefix), result.stdout

    node_str = result.stdout[len(expected_prefix):].strip()
    node_list = ast.literal_eval(node_str)
    assert is_circular_reversible_permutation(expected_nodes_in_cycle, node_list), f'Return: {result.stdout}'


def test_acyclic_region(monkeypatch):
    region = 'us-east-1'
    expected_return_code = 0

    monkeypatch.setenv("AWS_DEFAULT_REGION", region)
    env = os.environ.copy()

    result = subprocess.run(
        [
            sys.executable, "-m", "cycl", "check"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )

    assert result.returncode == expected_return_code, f"Return code: {result.returncode}\nStderr: {result.stderr}"

    # get this to run from the makefile
    # can i combine down to a single stage?
