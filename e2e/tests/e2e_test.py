import json
import os
import subprocess
import sys


def test_cyclic_region(monkeypatch):
    region = 'us-west-2'
    expected_return_code = 3  # cycle found
    expected_nodes_in_cycle = ['cyclic-stack-b', 'cyclic-stack-a']

    monkeypatch.setenv('AWS_DEFAULT_REGION', region)
    env = os.environ.copy()

    result = subprocess.run(
        [sys.executable, '-m', 'cycl', 'check', '--format', 'json'],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    assert result.returncode == expected_return_code, f'Non-zero exit: {result.returncode}\nStderr: {result.stderr}'
    cycles = json.loads(result.stdout)['cycles']
    # a two node cycle may start from either node
    assert len(cycles) == 1, f'Return: {result.stdout}'
    assert sorted(cycles[0]) == sorted(expected_nodes_in_cycle), f'Return: {result.stdout}'


def test_acyclic_region(monkeypatch):
    region = 'us-east-1'
    expected_return_code = 0

    monkeypatch.setenv('AWS_DEFAULT_REGION', region)
    env = os.environ.copy()

    result = subprocess.run(
        [sys.executable, '-m', 'cycl', 'check'],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    assert result.returncode == expected_return_code, f'Return code: {result.returncode}\nStderr: {result.stderr}'

    # get this to run from the makefile
    # can i combine down to a single stage?
    # create a role specifically for integration testing
    # always run the destroy infra step
    # run integration tests for change, beta version, and prod version
