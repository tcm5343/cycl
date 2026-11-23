import json
import os
import subprocess
import sys

import boto3

from cycl import build_graph, fetch_exports


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


def _cyclic_region_client():
    return boto3.client('cloudformation', region_name='us-west-2')


def test_fetch_exports_describe_stacks():
    exports = fetch_exports(cfn_client=_cyclic_region_client(), describe_stacks=True)

    export = exports['cyclic-stack-a-export-1']
    stacks = [export.exporting_stack, *export.importing_stacks]
    assert [stack.name for stack in stacks] == ['cyclic-stack-a', 'cyclic-stack-b']
    for stack in stacks:
        assert stack.id is not None, stack
        assert stack.id.startswith('arn:aws:cloudformation:us-west-2:'), stack
        assert stack.tags.get('cycl-e2e-group') == 'cyclic', stack

    graph = build_graph(exports, node_key_fn=lambda stack: stack.tags.get('cycl-e2e-group', stack.name))
    assert set(graph.nodes['cyclic']['stacks']) >= set(stacks)


def test_fetch_exports_excludes_tags_by_default():
    exports = fetch_exports(cfn_client=_cyclic_region_client())

    export = exports['cyclic-stack-a-export-1']
    assert export.exporting_stack.tags == {}
    assert all(stack.tags == {} for stack in export.importing_stacks)
