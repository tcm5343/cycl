from pathlib import Path
from unittest.mock import patch

import networkx as nx
import pytest

import cycl.cycl as cycl_module
from cycl.cycl import build_graph, get_graph_data
from cycl.models.export_data import ExportData
from cycl.utils.testing import is_circular_reversible_permutation


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
    with patch.object(ExportData, 'parse_name_from_id', autospec=True) as mock:
        mock.side_effect = lambda x: f'{x}-name'
        yield mock


@pytest.fixture(autouse=True)
def mock_get_all_exports():
    with patch.object(ExportData, 'get_all_exports', autospec=True) as mock:
        mock.return_value = {}
        yield mock


@pytest.fixture(autouse=True)
def mock_get_all_imports():
    with patch.object(ExportData, 'get_all_imports', autospec=True) as mock:
        mock.return_value = []
        yield mock


@pytest.fixture(autouse=True)
def mock_get_exports_from_assembly():
    with patch.object(cycl_module, 'get_exports_from_assembly', autospec=True) as mock:
        mock.return_value = {}
        yield mock


@pytest.fixture
def mock_get_graph_data():
    with patch.object(cycl_module, 'get_graph_data') as mock:
        mock.return_value = {}
        yield mock


def test_get_graph_data_returns_empty_graph_data():
    expected_graph_data = {}

    actual_graph = get_graph_data()
    assert actual_graph == expected_graph_data


def test_build_graph_returns_empty_graph():
    actual_graph = build_graph()

    assert nx.number_of_nodes(actual_graph) == 0
    assert nx.is_directed_acyclic_graph(actual_graph)
    assert next(nx.simple_cycles(actual_graph), []) == []


def test_build_graph_calls_get_graph_data_if_dep_graph_data_is_none(mock_get_graph_data):
    build_graph()
    mock_get_graph_data.assert_called_once()


def test_build_graph_does_not_call_get_graph_data_if_dep_graph_data_exists(
    mock_get_graph_data,
):
    build_graph(graph_data={})
    mock_get_graph_data.assert_not_called()


def test_get_graph_data_returns_some_graph_data(mock_get_all_exports, mock_get_all_imports):
    mock_get_all_exports.return_value = {
        'some-name-1': ExportData(
            stack_name='some-exporting-stack-id-1-name',
            stack_id='some-exporting-stack-id-1',
            export_name='some-name-1',
            export_value='some-value-1',
        )
    }

    def mock_get_all_imports_side_effect_func(self, cfn_client):  # noqa: ARG001
        self.importing_stacks = [
            ExportData(stack_name='some-importing-stack-name-1'),
            ExportData(stack_name='some-importing-stack-name-2'),
        ]

    mock_get_all_imports.side_effect = mock_get_all_imports_side_effect_func
    expected_graph_data = {
        'some-name-1': ExportData(
            stack_name='some-exporting-stack-id-1-name',
            stack_id='some-exporting-stack-id-1',
            export_name='some-name-1',
            export_value='some-value-1',
            importing_stacks=[
                ExportData(
                    stack_name='some-importing-stack-name-1',
                ),
                ExportData(
                    stack_name='some-importing-stack-name-2',
                ),
            ],
        )
    }

    actual_graph_data = get_graph_data()

    assert actual_graph_data == expected_graph_data
    mock_get_all_imports.assert_called_once()


def test_build_graph_returns_some_graph(subtests, mock_get_graph_data):
    graph_data = {
        'some-name-1': ExportData(
            stack_name='some-exporting-stack-id-1-name',
            stack_id='some-exporting-stack-id-1',
            export_name='some-name-1',
            export_value='some-value-1',
            importing_stacks=[
                ExportData(
                    stack_name='some-importing-stack-name-1',
                ),
                ExportData(
                    stack_name='some-importing-stack-name-2',
                ),
            ],
        )
    }
    mock_get_graph_data.return_value = graph_data
    expected_edges = [
        ('some-exporting-stack-id-1-name', 'some-importing-stack-name-1'),
        ('some-exporting-stack-id-1-name', 'some-importing-stack-name-2'),
    ]
    expected_nodes = [
        'some-exporting-stack-id-1-name',
        'some-importing-stack-name-1',
        'some-importing-stack-name-2',
    ]

    actual_graph = build_graph()

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


def test_get_graph_data_returns_graph_data_with_multiple_exports(mock_get_all_exports, mock_get_all_imports):
    mock_get_all_exports.return_value = {
        'some-name-1': ExportData(
            stack_id='some-exporting-stack-id-1',
            stack_name='some-exporting-stack-id-1-name',
            export_name='some-name-1',
            export_value='some-value-1',
        ),
        'some-name-2': ExportData(
            stack_id='some-exporting-stack-id-2',
            stack_name='some-exporting-stack-id-2-name',
            export_name='some-name-2',
            export_value='some-value-2',
        ),
    }

    def mock_get_all_imports_side_effect_func(self, cfn_client):  # noqa: ARG001
        if self.export_name == 'some-name-1':
            self.importing_stacks = [
                ExportData(stack_name='some-importing-stack-name-1'),
                ExportData(stack_name='some-importing-stack-name-2'),
            ]
        elif self.export_name == 'some-name-2':
            self.importing_stacks = [
                ExportData(stack_name='some-importing-stack-name-1'),
            ]

    mock_get_all_imports.side_effect = mock_get_all_imports_side_effect_func

    expected_graph_data = {
        'some-name-1': ExportData(
            stack_id='some-exporting-stack-id-1',
            stack_name='some-exporting-stack-id-1-name',
            export_name='some-name-1',
            export_value='some-value-1',
            importing_stacks=[
                ExportData(
                    stack_name='some-importing-stack-name-1',
                ),
                ExportData(
                    stack_name='some-importing-stack-name-2',
                ),
            ],
        ),
        'some-name-2': ExportData(
            stack_id='some-exporting-stack-id-2',
            stack_name='some-exporting-stack-id-2-name',
            export_name='some-name-2',
            export_value='some-value-2',
            importing_stacks=[
                ExportData(
                    stack_name='some-importing-stack-name-1',
                ),
            ],
        ),
    }

    actual_graph_data = get_graph_data()
    print(actual_graph_data['some-name-1'].importing_stacks)
    assert actual_graph_data == expected_graph_data
    assert mock_get_all_imports.call_count == 2


def test_build_graph_returns_graph_with_multiple_exports(subtests, mock_get_graph_data):
    graph_data = {
        'some-name-1': ExportData(
            stack_id='some-exporting-stack-id-1',
            stack_name='some-exporting-stack-id-1-name',
            export_name='some-name-1',
            export_value='some-value-1',
            importing_stacks=[
                ExportData(
                    stack_name='some-importing-stack-name-1',
                ),
                ExportData(
                    stack_name='some-importing-stack-name-2',
                ),
            ],
        ),
        'some-name-2': ExportData(
            stack_id='some-exporting-stack-id-2',
            stack_name='some-exporting-stack-id-2-name',
            export_name='some-name-2',
            export_value='some-value-2',
            importing_stacks=[
                ExportData(
                    stack_name='some-importing-stack-name-1',
                ),
            ],
        ),
    }
    mock_get_graph_data.return_value = graph_data
    expected_edges = [
        ('some-exporting-stack-id-1-name', 'some-importing-stack-name-1'),
        ('some-exporting-stack-id-1-name', 'some-importing-stack-name-2'),
        ('some-exporting-stack-id-2-name', 'some-importing-stack-name-1'),
    ]
    expected_nodes = [
        'some-exporting-stack-id-1-name',
        'some-exporting-stack-id-2-name',
        'some-importing-stack-name-1',
        'some-importing-stack-name-2',
    ]

    actual_graph = build_graph()

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


def test_get_graph_data_returns_graph_data_when_export_has_no_imports(mock_get_all_exports, mock_get_all_imports):
    mock_get_all_exports.return_value = {
        'some-name-1': ExportData(
            stack_id='some-exporting-stack-id-1',
            stack_name='some-exporting-stack-id-1-name',
            export_name='some-name-1',
            export_value='some-value-1',
        ),
    }

    def mock_get_all_imports_side_effect_func(self, cfn_client):  # noqa: ARG001
        self.importing_stacks = []

    mock_get_all_imports.side_effect = mock_get_all_imports_side_effect_func

    expected_graph_data = {
        'some-name-1': ExportData(
            stack_id='some-exporting-stack-id-1',
            stack_name='some-exporting-stack-id-1-name',
            export_name='some-name-1',
            export_value='some-value-1',
            importing_stacks=[],
        )
    }

    actual_graph_data = get_graph_data()
    assert actual_graph_data == expected_graph_data
    mock_get_all_imports.assert_called_once()


def test_build_graph_returns_graph_when_export_has_no_imports(subtests, mock_get_graph_data):
    graph_data = {
        'some-name-1': ExportData(
            stack_id='some-exporting-stack-id-1',
            stack_name='some-exporting-stack-id-1-name',
            export_name='some-name-1',
            export_value='some-value-1',
            importing_stacks=[],
        )
    }
    mock_get_graph_data.return_value = graph_data
    expected_edges = []
    expected_nodes = ['some-exporting-stack-id-1-name']

    actual_graph = build_graph()

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


def test_get_graph_data_returns_empty_graph_data_with_cdk_out_path(mock_get_exports_from_assembly):
    actual_graph_data = get_graph_data(cdk_out_path='some-cdk-out-path')
    assert actual_graph_data == {}
    mock_get_exports_from_assembly.assert_called_once_with(Path('some-cdk-out-path'))


def test_get_graph_data_returns_graph_data_with_cdk_out_path(
    mock_get_all_exports, mock_get_all_imports, mock_get_exports_from_assembly
):
    mock_get_exports_from_assembly.return_value = {
        'some-name-1': [
            ExportData(
                stack_name='some-cdk-out-stack-name-1',
            )
        ],
    }
    mock_get_all_exports.return_value = {
        'some-name-1': ExportData(
            stack_id='some-exporting-stack-id-1',
            stack_name='some-exporting-stack-id-1-name',
            export_name='some-name-1',
            export_value='some-value-1',
        ),
    }

    def mock_get_all_imports_side_effect_func(self, cfn_client):  # noqa: ARG001
        self.importing_stacks = [
            ExportData(stack_name='some-importing-stack-name-1'),
            ExportData(stack_name='some-importing-stack-name-2'),
        ]

    mock_get_all_imports.side_effect = mock_get_all_imports_side_effect_func
    expected_graph_data = {
        'some-name-1': ExportData(
            stack_id='some-exporting-stack-id-1',
            stack_name='some-exporting-stack-id-1-name',
            export_name='some-name-1',
            export_value='some-value-1',
            importing_stacks=[
                ExportData(
                    stack_name='some-importing-stack-name-1',
                ),
                ExportData(
                    stack_name='some-importing-stack-name-2',
                ),
                ExportData(
                    stack_name='some-cdk-out-stack-name-1',
                ),
            ],
        ),
    }

    actual_graph_data = get_graph_data(cdk_out_path='some-cdk-out-path')

    mock_get_exports_from_assembly.assert_called_once_with(Path('some-cdk-out-path'))
    mock_get_all_imports.assert_called_once()
    assert actual_graph_data == expected_graph_data


def test_get_graph_data_returns_graph_data_with_cdk_out_path_and_no_existing_exports(
    mock_get_all_exports, mock_get_all_imports, mock_get_exports_from_assembly
):
    """Handles the case where an export is missing during the first deployment.

    If we are deploying for the first time and have two independent stacks: stack1 and stack2. stack1 creates an
    export and stack2 imports it, with dependsOn(), this will deploy successfully. We are unable to find the imported
    export so it should be safe to ignore in our graph.
    """
    mock_get_exports_from_assembly.return_value = {
        'some-name-1': [
            ExportData(
                stack_name='some-cdk-out-stack-name-1',
            )
        ],
    }

    def mock_get_all_imports_side_effect_func(self, cfn_client):  # noqa: ARG001
        self.importing_stacks = []

    mock_get_all_imports.side_effect = mock_get_all_imports_side_effect_func
    mock_get_all_exports.return_value = {}
    expected_graph_data = {}

    actual_graph_data = get_graph_data(cdk_out_path='some-cdk-out-path')

    mock_get_all_imports.assert_not_called()
    assert actual_graph_data == expected_graph_data


def test_config_defined_as_expected(mock_config, mock_boto3):
    get_graph_data()

    mock_config.assert_called_once_with(
        retries={
            'max_attempts': 10,
            'mode': 'adaptive',
        },
    )
    mock_boto3.client.assert_called_once_with('cloudformation', config=mock_config.return_value)


def test_build_graph_returns_cyclic_graph(mock_get_graph_data, subtests, mock_get_exports_from_assembly):
    graph_data = {
        'some-name-1': ExportData(
            stack_id='some-exporting-stack-id-1',
            stack_name='some-exporting-stack-id-1-name',
            export_name='some-name-1',
            export_value='some-value-1',
            importing_stacks=[
                ExportData(stack_name='some-exporting-stack-id-2-name'),
            ],
        ),
        'some-name-2': ExportData(
            stack_id='some-exporting-stack-id-2',
            stack_name='some-exporting-stack-id-2-name',
            export_name='some-name-2',
            export_value='some-value-2',
            importing_stacks=[
                ExportData(stack_name='some-exporting-stack-id-1-name'),
            ],
        ),
    }
    mock_get_graph_data.return_value = graph_data
    expected_edges = [
        ('some-exporting-stack-id-1-name', 'some-exporting-stack-id-2-name'),
        ('some-exporting-stack-id-2-name', 'some-exporting-stack-id-1-name'),
    ]
    expected_nodes = [
        'some-exporting-stack-id-1-name',
        'some-exporting-stack-id-2-name',
    ]
    expected_cycles = [['some-exporting-stack-id-2-name', 'some-exporting-stack-id-1-name']]

    actual_graph = build_graph()

    mock_get_exports_from_assembly.assert_not_called()
    for expected_node in expected_nodes:
        with subtests.test(msg='assert graph has node', expected_node=expected_node):
            assert actual_graph.has_node(expected_node)
    assert nx.number_of_nodes(actual_graph) == len(expected_nodes)

    for expected_edge in expected_edges:
        with subtests.test(msg='assert graph has edge', expected_edge=expected_edge):
            assert actual_graph.has_edge(*expected_edge)
    assert nx.number_of_edges(actual_graph) == len(expected_edges)

    assert not nx.is_directed_acyclic_graph(actual_graph)
    actual_cycles = list(nx.simple_cycles(actual_graph))

    for expected_cycle in expected_cycles:
        with subtests.test(msg='assert cycle is expected', expected_cycles=expected_cycles):
            assert any(is_circular_reversible_permutation(actual_cycle, expected_cycle) for actual_cycle in actual_cycles)

    assert len(actual_cycles) == len(expected_cycles)


def test_build_graph_make_cyclic_graph_acyclic_with_ignore_nodes(
    mock_get_graph_data, subtests, mock_get_exports_from_assembly
):
    graph_data = {
        'some-name-1': ExportData(
            stack_id='some-exporting-stack-id-1',
            stack_name='some-exporting-stack-id-1-name',
            export_name='some-name-1',
            export_value='some-value-1',
            importing_stacks=[
                ExportData(stack_name='some-exporting-stack-id-2-name'),
                ExportData(stack_name='some-importing-stack-id-3-name'),
            ],
        ),
        'some-name-2': ExportData(
            stack_id='some-exporting-stack-id-2',
            stack_name='some-exporting-stack-id-2-name',
            export_name='some-name-2',
            export_value='some-value-2',
            importing_stacks=[
                ExportData(stack_name='some-exporting-stack-id-1-name'),
            ],
        ),
    }
    mock_get_graph_data.return_value = graph_data
    expected_edges = [
        ('some-exporting-stack-id-1-name', 'some-importing-stack-id-3-name'),
    ]
    expected_nodes = [
        'some-exporting-stack-id-1-name',
        'some-importing-stack-id-3-name',
    ]

    actual_graph = build_graph(nodes_to_ignore=['some-exporting-stack-id-2-name'])

    mock_get_exports_from_assembly.assert_not_called()
    for expected_node in expected_nodes:
        with subtests.test(msg='assert graph has node', expected_node=expected_node):
            assert actual_graph.has_node(expected_node)
    assert nx.number_of_nodes(actual_graph) == len(expected_nodes)

    for expected_edge in expected_edges:
        with subtests.test(msg='assert graph has edge', expected_edge=expected_edge):
            assert actual_graph.has_edge(*expected_edge)
    assert nx.number_of_edges(actual_graph) == len(expected_edges)

    assert nx.is_directed_acyclic_graph(actual_graph)
    assert list(nx.simple_cycles(actual_graph)) == []


def test_build_graph_make_cyclic_graph_acyclic_with_ignore_edges(
    mock_get_graph_data, subtests, mock_get_exports_from_assembly
):
    graph_data = {
        'some-name-1': ExportData(
            stack_id='some-exporting-stack-id-1',
            stack_name='some-exporting-stack-id-1-name',
            export_name='some-name-1',
            export_value='some-value-1',
            importing_stacks=[
                ExportData(stack_name='some-exporting-stack-id-2-name'),
            ],
        ),
        'some-name-2': ExportData(
            stack_id='some-exporting-stack-id-2',
            stack_name='some-exporting-stack-id-2-name',
            export_name='some-name-2',
            export_value='some-value-2',
            importing_stacks=[
                ExportData(stack_name='some-exporting-stack-id-1-name'),
            ],
        ),
    }
    mock_get_graph_data.return_value = graph_data
    expected_edges = [
        ('some-exporting-stack-id-1-name', 'some-exporting-stack-id-2-name'),
    ]
    expected_nodes = [
        'some-exporting-stack-id-1-name',
        'some-exporting-stack-id-2-name',
    ]

    actual_graph = build_graph(
        edges_to_ignore=[
            ['some-exporting-stack-id-2-name', 'some-exporting-stack-id-1-name'],
        ]
    )

    mock_get_exports_from_assembly.assert_not_called()
    for expected_node in expected_nodes:
        with subtests.test(msg='assert graph has node', expected_node=expected_node):
            assert actual_graph.has_node(expected_node)
    assert nx.number_of_nodes(actual_graph) == len(expected_nodes)

    for expected_edge in expected_edges:
        with subtests.test(msg='assert graph has edge', expected_edge=expected_edge):
            assert actual_graph.has_edge(*expected_edge)
    assert nx.number_of_edges(actual_graph) == len(expected_edges)

    assert nx.is_directed_acyclic_graph(actual_graph)
    assert list(nx.simple_cycles(actual_graph)) == []
