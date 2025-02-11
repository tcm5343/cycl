from pathlib import Path
from unittest.mock import patch

import networkx as nx
import pytest

import cycl.cycl as cycl_module
from cycl.cycl import build_dependency_graph


@pytest.fixture(autouse=True)
def mock_boto3():
    with patch.object(cycl_module, 'boto3') as mock:
        yield mock


@pytest.fixture(autouse=True)
def mock_config():
    with patch.object(cycl_module, 'Config') as mock:
        yield mock


@pytest.fixture(autouse=True)
def mock_parse_name_from_id():
    with patch.object(cycl_module, 'parse_name_from_id') as mock:
        mock.side_effect = lambda x: f'{x}-stack-name'
        yield mock


@pytest.fixture(autouse=True)
def mock_get_all_exports():
    with patch.object(cycl_module, 'get_all_exports') as mock:
        mock.return_value = {}
        yield mock


@pytest.fixture(autouse=True)
def mock_get_all_imports():
    with patch.object(cycl_module, 'get_all_imports') as mock:
        mock.return_value = []
        yield mock


@pytest.fixture(autouse=True)
def mock_get_cdk_out_imports():
    with patch.object(cycl_module, 'get_cdk_out_imports') as mock:
        mock.return_value = {}
        yield mock


def test_build_dependency_graph_returns_empty_graph():
    actual_graph = build_dependency_graph()

    assert nx.number_of_nodes(actual_graph) == 0
    assert nx.is_directed_acyclic_graph(actual_graph)
    assert next(nx.simple_cycles(actual_graph), []) == []


def test_build_dependency_graph_returns_graph(
    mock_get_all_exports, mock_get_all_imports, subtests, mock_get_cdk_out_imports
):
    """
    Visual representation of expected output graph:
    some-exporting-stack-id-1-stack-name
        │
        ├──► some-importing-stack-name-1
        │
        ├──► some-importing-stack-name-2
    """
    mock_get_all_exports.return_value = {
        'some-name-1': {
            'ExportingStackId': 'some-exporting-stack-id-1',
            'Name': 'some-name-1',
            'Value': 'some-value-1',
        },
    }
    mock_get_all_imports.return_value = [
        'some-importing-stack-name-1',
        'some-importing-stack-name-2',
    ]
    expected_edges = [
        ('some-exporting-stack-id-1-stack-name', 'some-importing-stack-name-1'),
        ('some-exporting-stack-id-1-stack-name', 'some-importing-stack-name-2'),
    ]
    expected_nodes = [
        'some-exporting-stack-id-1-stack-name',
        'some-importing-stack-name-1',
        'some-importing-stack-name-2',
    ]

    actual_graph = build_dependency_graph()

    mock_get_cdk_out_imports.assert_not_called()
    for expected_node in expected_nodes:
        with subtests.test(msg='assert graph has node', expected_node=expected_node):
            assert actual_graph.has_node(expected_node)
    assert nx.number_of_nodes(actual_graph) == len(expected_nodes)

    for expected_edge in expected_edges:
        with subtests.test(msg='assert graph has edge', expected_edge=expected_edge):
            assert actual_graph.has_edge(*expected_edge)
    assert nx.number_of_edges(actual_graph) == len(expected_edges)

    assert nx.is_directed_acyclic_graph(actual_graph)
    assert next(nx.simple_cycles(actual_graph), []) == []


def test_build_dependency_graph_returns_graph_with_multiple_exports(mock_get_all_exports, mock_get_all_imports, subtests):
    """
    Visual representation of expected output graph:
    some-exporting-stack-id-1-stack-name
        │
        ├──► some-importing-stack-name-1
        │
        ├──► some-importing-stack-name-2

    some-exporting-stack-id-2-stack-name
            │
            ├──► some-importing-stack-name-1

    some-exporting-stack-id-3-stack-name  (No outgoing edges)
    some-importing-stack-name-1  (No outgoing edges)
    some-importing-stack-name-2  (No outgoing edges)
    """
    mock_get_all_exports.return_value = {
        'some-name-1': {
            'ExportingStackId': 'some-exporting-stack-id-1',
            'Name': 'some-name-1',
            'Value': 'some-value-1',
        },
        'some-name-2': {
            'ExportingStackId': 'some-exporting-stack-id-2',
            'Name': 'some-name-2',
            'Value': 'some-value-2',
        },
    }

    def mock_get_all_imports_side_effect_func(export_name, *_args, **_kwargs):
        if export_name == 'some-name-1':
            return [
                'some-importing-stack-name-1',
                'some-importing-stack-name-2',
            ]
        if export_name == 'some-name-2':
            return [
                'some-importing-stack-name-1',
            ]
        return []  # handles export with no import

    mock_get_all_imports.side_effect = mock_get_all_imports_side_effect_func
    expected_edges = [
        ('some-exporting-stack-id-1-stack-name', 'some-importing-stack-name-1'),
        ('some-exporting-stack-id-1-stack-name', 'some-importing-stack-name-2'),
        ('some-exporting-stack-id-2-stack-name', 'some-importing-stack-name-1'),
    ]
    expected_nodes = [
        'some-exporting-stack-id-1-stack-name',
        'some-exporting-stack-id-2-stack-name',
        'some-importing-stack-name-1',
        'some-importing-stack-name-2',
    ]

    actual_graph = build_dependency_graph()

    for expected_node in expected_nodes:
        with subtests.test(msg='assert graph has node', expected_node=expected_node):
            assert actual_graph.has_node(expected_node)
    assert nx.number_of_nodes(actual_graph) == len(expected_nodes)

    for expected_edge in expected_edges:
        with subtests.test(msg='assert graph has edge', expected_edge=expected_edge):
            assert actual_graph.has_edge(*expected_edge)
    assert nx.number_of_edges(actual_graph) == len(expected_edges)

    assert nx.is_directed_acyclic_graph(actual_graph)
    assert next(nx.simple_cycles(actual_graph), []) == []


def test_build_dependency_graph_returns_graph_when_export_has_no_imports(
    mock_get_all_exports, mock_get_all_imports, subtests
):
    """
    Visual representation of expected output graph:
    some-exporting-stack-id-1-stack-name  (No outgoing edges)
    """
    mock_get_all_exports.return_value = {
        'some-name-1': {
            'ExportingStackId': 'some-exporting-stack-id-1',
            'Name': 'some-name-1',
            'Value': 'some-value-1',
        },
    }
    mock_get_all_imports.return_value = []
    expected_edges = []
    expected_nodes = ['some-exporting-stack-id-1-stack-name']

    actual_graph = build_dependency_graph()

    for expected_node in expected_nodes:
        with subtests.test(msg='assert graph has node', expected_node=expected_node):
            assert actual_graph.has_node(expected_node)
    assert nx.number_of_nodes(actual_graph) == len(expected_nodes)

    for expected_edge in expected_edges:
        with subtests.test(msg='assert graph has edge', expected_edge=expected_edge):
            assert actual_graph.has_edge(*expected_edge)
    assert nx.number_of_edges(actual_graph) == len(expected_edges)

    assert nx.is_directed_acyclic_graph(actual_graph)
    assert next(nx.simple_cycles(actual_graph), []) == []


def test_build_dependency_graph_returns_empty_graph_with_cdk_out_path(mock_get_cdk_out_imports):
    actual_graph = build_dependency_graph(cdk_out_path='some-cdk-out-path')

    mock_get_cdk_out_imports.assert_called_once_with(Path('some-cdk-out-path'))
    assert nx.number_of_nodes(actual_graph) == 0
    assert nx.is_directed_acyclic_graph(actual_graph)
    assert next(nx.simple_cycles(actual_graph), []) == []


def test_build_dependency_graph_returns_graph_with_cdk_out_path(
    mock_get_all_exports, mock_get_all_imports, subtests, mock_get_cdk_out_imports
):
    """
    Visual representation of expected output graph:
    some-exporting-stack-id-1-stack-name
        │
        ├──► some-importing-stack-name-1
        │
        ├──► some-importing-stack-name-2
        │
        ├──► some-cdk-out-stack-name-1
    """
    mock_get_cdk_out_imports.return_value = {'some-name-1': ['some-cdk-out-stack-name-1']}
    mock_get_all_exports.return_value = {
        'some-name-1': {
            'ExportingStackId': 'some-exporting-stack-id-1',
            'Name': 'some-name-1',
            'Value': 'some-value-1',
        },
    }
    mock_get_all_imports.return_value = [
        'some-importing-stack-name-1',
        'some-importing-stack-name-2',
    ]
    expected_edges = [
        ('some-exporting-stack-id-1-stack-name', 'some-importing-stack-name-1'),
        ('some-exporting-stack-id-1-stack-name', 'some-importing-stack-name-2'),
        ('some-exporting-stack-id-1-stack-name', 'some-cdk-out-stack-name-1'),
    ]
    expected_nodes = [
        'some-exporting-stack-id-1-stack-name',
        'some-importing-stack-name-1',
        'some-importing-stack-name-2',
        'some-cdk-out-stack-name-1',
    ]

    actual_graph = build_dependency_graph(cdk_out_path='some-cdk-out-path')

    mock_get_cdk_out_imports.assert_called_once_with(Path('some-cdk-out-path'))
    for expected_node in expected_nodes:
        with subtests.test(msg='assert graph has node', expected_node=expected_node):
            assert actual_graph.has_node(expected_node)
    assert nx.number_of_nodes(actual_graph) == len(expected_nodes)

    for expected_edge in expected_edges:
        with subtests.test(msg='assert graph has edge', expected_edge=expected_edge):
            assert actual_graph.has_edge(*expected_edge)
    assert nx.number_of_edges(actual_graph) == len(expected_edges)

    assert nx.is_directed_acyclic_graph(actual_graph)
    assert next(nx.simple_cycles(actual_graph), []) == []


def test_build_dependency_graph_returns_graph_with_cdk_out_path_and_no_existing_exports(
    mock_get_all_exports, mock_get_all_imports, subtests, mock_get_cdk_out_imports
):
    """
    If we are deploying for the first time and have two independent stacks: stack1 and stack2. stack1 creates
    an export and stack1 imports it, with dependsOn(), this will deploy successfully. We are unable to find
    the imported export so it should be safe to ignore in our graph.
    """
    mock_get_cdk_out_imports.return_value = {'some-name-1': ['some-cdk-out-stack-name-1']}
    mock_get_all_exports.return_value = {}
    mock_get_all_imports.return_value = []
    expected_edges = []
    expected_nodes = []

    actual_graph = build_dependency_graph(cdk_out_path='some-cdk-out-path')

    mock_get_cdk_out_imports.assert_called_once_with(Path('some-cdk-out-path'))
    for expected_node in expected_nodes:
        with subtests.test(msg='assert graph has node', expected_node=expected_node):
            assert actual_graph.has_node(expected_node)
    assert nx.number_of_nodes(actual_graph) == len(expected_nodes)

    for expected_edge in expected_edges:
        with subtests.test(msg='assert graph has edge', expected_edge=expected_edge):
            assert actual_graph.has_edge(*expected_edge)
    assert nx.number_of_edges(actual_graph) == len(expected_edges)

    assert nx.is_directed_acyclic_graph(actual_graph)
    assert next(nx.simple_cycles(actual_graph), []) == []


def test_config_defined_as_expected(mock_config, mock_boto3):
    build_dependency_graph()

    mock_config.assert_called_once_with(
        retries={
            'max_attempts': 10,
            'mode': 'adaptive',
        },
    )
    mock_boto3.client.assert_called_once_with('cloudformation', config=mock_config.return_value)
