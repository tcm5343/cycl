import json
import os
import subprocess
import sys

import boto3
import pytest

from cycl import build_graph, fetch_exports

CYCLIC_REGION = 'us-west-2'  # cyclic-stack-a and cyclic-stack-b import from each other
ACYCLIC_REGION = 'us-east-1'  # acyclic-stack has an export nothing imports
STACK_A = 'cyclic-stack-a'
STACK_B = 'cyclic-stack-b'
ACYCLIC_STACK = 'acyclic-stack'
# stacks AWS creates in the account rather than e2e/infra, which can have exports of their own
AWS_MANAGED_STACKS = [
    'CDKToolkit',  # created by `cdk bootstrap`
]
IGNORE_AWS_MANAGED_STACKS = [arg for stack in AWS_MANAGED_STACKS for arg in ('--ignore-node', stack)]
EXIT_OK = 0
EXIT_CYCLE_FOUND = 3


def run_cycl(*args, region):
    return subprocess.run(
        [sys.executable, '-m', 'cycl', *args],
        capture_output=True,
        text=True,
        env={**os.environ, 'AWS_DEFAULT_REGION': region},
        check=False,
    )


def describe(result):
    return f'exit code: {result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}'


def test_cyclic_region():
    result = run_cycl('check', '--format', 'json', region=CYCLIC_REGION)

    assert result.returncode == EXIT_CYCLE_FOUND, describe(result)
    cycles = json.loads(result.stdout)['cycles']
    # a two node cycle may start from either node
    assert [sorted(cycle) for cycle in cycles] == [[STACK_A, STACK_B]], describe(result)


def test_acyclic_region():
    result = run_cycl('check', region=ACYCLIC_REGION)

    assert result.returncode == EXIT_OK, describe(result)
    assert result.stdout == '', describe(result)


@pytest.mark.parametrize('command', ['check', 'topo'])
def test_text_format_cyclic_region(command):
    result = run_cycl(command, '--format', 'text', region=CYCLIC_REGION)

    assert result.returncode == EXIT_CYCLE_FOUND, describe(result)
    lines = result.stdout.splitlines()
    assert len(lines) == 1, describe(result)
    assert lines[0].startswith('cycle found between nodes: '), describe(result)
    assert STACK_A in lines[0], describe(result)
    assert STACK_B in lines[0], describe(result)


def test_topo_cyclic_region():
    result = run_cycl('topo', '--format', 'json', region=CYCLIC_REGION)

    assert result.returncode == EXIT_CYCLE_FOUND, describe(result)
    output = json.loads(result.stdout)
    assert [sorted(cycle) for cycle in output['cycles']] == [[STACK_A, STACK_B]], describe(result)
    assert output['generations'] is None, describe(result)
    assert 'graph is cyclic' in result.stderr, describe(result)


def test_topo_acyclic_region():
    json_result = run_cycl('topo', '--format', 'json', region=ACYCLIC_REGION)
    text_result = run_cycl('topo', '--format', 'text', region=ACYCLIC_REGION)

    assert json_result.returncode == EXIT_OK, describe(json_result)
    output = json.loads(json_result.stdout)
    assert output['cycles'] == [], describe(json_result)
    assert ACYCLIC_STACK in [node for generation in output['generations'] for node in generation], describe(json_result)

    assert text_result.returncode == EXIT_OK, describe(text_result)
    # one line per generation, nodes separated by spaces
    assert ACYCLIC_STACK in text_result.stdout.split(), describe(text_result)


@pytest.mark.parametrize('node', [STACK_A, STACK_B])
def test_ignore_node_breaks_cycle(node):
    result = run_cycl('check', '--format', 'json', '--ignore-node', node, region=CYCLIC_REGION)

    assert result.returncode == EXIT_OK, describe(result)
    assert json.loads(result.stdout)['cycles'] == [], describe(result)


@pytest.mark.parametrize(
    ('edge', 'expected_generations'),
    [
        # edges point from the exporting to the importing stack, so ignoring a -> b leaves b -> a: b comes first
        ((STACK_A, STACK_B), [[STACK_B], [STACK_A]]),
        ((STACK_B, STACK_A), [[STACK_A], [STACK_B]]),
    ],
)
def test_ignore_edge_breaks_cycle(edge, expected_generations):
    result = run_cycl('topo', '--format', 'json', '--ignore-edge', *edge, *IGNORE_AWS_MANAGED_STACKS, region=CYCLIC_REGION)

    assert result.returncode == EXIT_OK, describe(result)
    assert json.loads(result.stdout) == {'cycles': [], 'generations': expected_generations}, describe(result)


def _cyclic_region_client():
    return boto3.client('cloudformation', region_name='us-west-2')


def test_fetch_exports_describe_stacks(subtests):
    exports = fetch_exports(cfn_client=_cyclic_region_client(), describe_stacks=True)

    export = exports['cyclic-stack-a-export-1']
    stacks = [export.exporting_stack, *export.importing_stacks]
    assert [stack.name for stack in stacks] == [STACK_A, STACK_B]
    for stack in stacks:
        with subtests.test(stack=stack.name):
            assert stack.id is not None, stack
            assert stack.id.startswith('arn:aws:cloudformation:us-west-2:'), stack
            assert stack.tags.get('cycl-e2e-group') == 'cyclic', stack

    graph = build_graph(exports, node_key_fn=lambda stack: stack.tags.get('cycl-e2e-group', stack.name))
    assert set(graph.nodes['cyclic']['stacks']) >= set(stacks)


def test_fetch_exports_excludes_tags_by_default(subtests):
    exports = fetch_exports(cfn_client=_cyclic_region_client())

    export = exports['cyclic-stack-a-export-1']
    stacks = [export.exporting_stack, *export.importing_stacks]
    assert [stack.name for stack in stacks] == [STACK_A, STACK_B]
    for stack in stacks:
        with subtests.test(stack=stack.name):
            assert stack.tags == {}, stack
