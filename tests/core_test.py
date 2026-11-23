import logging
from unittest.mock import Mock, call, patch

import networkx as nx
import pytest

import cycl._core as core_module
from cycl import Export, Stack, build_graph, fetch_exports


def _export(name, exporter, importers=()):
    return Export(
        name=name,
        value=f'{name}-value',
        exporting_stack=Stack(name=exporter, id=f'arn:{exporter}'),
        importing_stacks=tuple(Stack(name=importer) for importer in importers),
    )


def _exports(*exports):
    return {export.name: export for export in exports}


@pytest.fixture(autouse=True)
def mock_boto3():
    with patch.object(core_module, 'boto3') as mock:
        yield mock


@pytest.fixture(autouse=True)
def mock_list_exports():
    with patch.object(core_module, 'list_exports', autospec=True) as mock:
        mock.return_value = {}
        yield mock


@pytest.fixture(autouse=True)
def mock_list_importing_stacks():
    with patch.object(core_module, 'list_importing_stacks', autospec=True) as mock:
        mock.return_value = []
        yield mock


# fetch_exports


def test_fetch_exports_returns_empty_exports():
    assert fetch_exports() == {}


def test_fetch_exports_creates_client_with_retry_config(mock_boto3, mock_list_exports):
    fetch_exports()

    mock_boto3.client.assert_called_once()
    assert mock_boto3.client.call_args.args == ('cloudformation',)
    assert mock_boto3.client.call_args.kwargs['config'].retries == {'max_attempts': 10, 'mode': 'adaptive'}
    mock_list_exports.assert_called_once_with(mock_boto3.client.return_value)


def test_fetch_exports_uses_provided_client(mock_boto3, mock_list_exports, mock_list_importing_stacks):
    cfn_client = Mock(name='cfn_client')
    mock_list_exports.return_value = _exports(_export('export-1', 'stack-a'))

    fetch_exports(cfn_client=cfn_client)

    mock_boto3.client.assert_not_called()
    mock_list_exports.assert_called_once_with(cfn_client)
    mock_list_importing_stacks.assert_called_once_with(cfn_client, 'export-1')


def test_fetch_exports_is_keyword_only():
    with pytest.raises(TypeError):
        fetch_exports(Mock())  # type: ignore[misc]


def test_fetch_exports_adds_importing_stacks(mock_list_exports, mock_list_importing_stacks):
    mock_list_exports.return_value = _exports(_export('export-1', 'stack-a'), _export('export-2', 'stack-b'))
    mock_list_importing_stacks.side_effect = lambda _client, name: {
        'export-1': [Stack(name='stack-b'), Stack(name='stack-c')],
        'export-2': [Stack(name='stack-c')],
    }[name]

    actual = fetch_exports()

    assert actual == _exports(
        _export('export-1', 'stack-a', ['stack-b', 'stack-c']),
        _export('export-2', 'stack-b', ['stack-c']),
    )


def test_fetch_exports_warns_when_export_has_no_imports(caplog, mock_list_exports):
    mock_list_exports.return_value = _exports(_export('export-1', 'stack-a'))

    with caplog.at_level(logging.WARNING):
        actual = fetch_exports()

    assert actual == _exports(_export('export-1', 'stack-a'))
    assert 'Export found with no import: export-1 from stack-a' in caplog.text


# build_graph


def _assert_graph(graph, nodes, edges):
    assert set(graph.nodes) == set(nodes)
    assert sorted(graph.edges(keys=True)) == sorted(edges)


def test_build_graph_returns_empty_graph():
    graph = build_graph({})

    assert isinstance(graph, nx.MultiDiGraph)
    assert nx.number_of_nodes(graph) == 0


def test_build_graph_requires_exports():
    with pytest.raises(TypeError):
        build_graph()  # type: ignore[call-arg]


def test_build_graph_options_are_keyword_only():
    with pytest.raises(TypeError):
        build_graph({}, lambda x: x.name)  # type: ignore[misc]


def test_build_graph_returns_some_graph():
    graph = build_graph(_exports(_export('export-1', 'stack-a', ['stack-b', 'stack-c'])))

    _assert_graph(
        graph,
        nodes=['stack-a', 'stack-b', 'stack-c'],
        edges=[('stack-a', 'stack-b', 'export-1'), ('stack-a', 'stack-c', 'export-1')],
    )
    assert nx.is_directed_acyclic_graph(graph)


def test_build_graph_keys_parallel_edges_by_export_name():
    data = _exports(_export('export-1', 'stack-a', ['stack-b']), _export('export-2', 'stack-a', ['stack-b']))

    graph = build_graph(data)

    _assert_graph(
        graph,
        nodes=['stack-a', 'stack-b'],
        edges=[('stack-a', 'stack-b', 'export-1'), ('stack-a', 'stack-b', 'export-2')],
    )
    assert graph.edges['stack-a', 'stack-b', 'export-1']['export'] == data['export-1']
    assert graph.edges['stack-a', 'stack-b', 'export-2']['export'] == data['export-2']


def test_build_graph_includes_export_with_no_imports():
    data = _exports(_export('export-1', 'stack-a'))

    graph = build_graph(data)

    _assert_graph(graph, nodes=['stack-a'], edges=[])
    assert graph.nodes['stack-a']['exports'] == {'export-1': data['export-1']}


def test_build_graph_node_attributes():
    data = _exports(
        _export('export-1', 'stack-a', ['stack-b']),
        _export('export-2', 'stack-b', ['stack-c']),
    )

    graph = build_graph(data)

    assert graph.nodes['stack-a'] == {'stacks': {Stack(name='stack-a')}, 'exports': {'export-1': data['export-1']}}
    assert graph.nodes['stack-b'] == {'stacks': {Stack(name='stack-b')}, 'exports': {'export-2': data['export-2']}}
    assert graph.nodes['stack-c'] == {'stacks': {Stack(name='stack-c')}, 'exports': {}}


def test_build_graph_returns_cyclic_graph(is_circular_reversible_permutation):
    graph = build_graph(
        _exports(
            _export('export-1', 'stack-a', ['stack-b']),
            _export('export-2', 'stack-b', ['stack-c']),
            _export('export-3', 'stack-c', ['stack-a']),
        )
    )

    cycles = list(nx.simple_cycles(graph))
    assert len(cycles) == 1
    assert is_circular_reversible_permutation(['stack-a', 'stack-b', 'stack-c'], cycles[0])


def test_build_graph_ignore_nodes():
    data = _exports(
        _export('export-1', 'stack-a', ['stack-b', 'stack-c']),
        _export('export-2', 'stack-b', ['stack-a']),
    )

    graph = build_graph(data, ignore_nodes=['stack-b'])

    _assert_graph(graph, nodes=['stack-a', 'stack-c'], edges=[('stack-a', 'stack-c', 'export-1')])


@pytest.mark.parametrize('edge', [('stack-b', 'stack-a'), ['stack-b', 'stack-a']])
def test_build_graph_ignore_edges(edge):
    data = _exports(
        _export('export-1', 'stack-a', ['stack-b']),
        _export('export-2', 'stack-b', ['stack-a']),
    )

    graph = build_graph(data, ignore_edges=[edge])

    _assert_graph(graph, nodes=['stack-a', 'stack-b'], edges=[('stack-a', 'stack-b', 'export-1')])


def _selfloop_data():
    return _exports(
        _export('export-1', 'stack-a1', ['stack-a2']),
        _export('export-2', 'stack-a2', ['stack-b']),
    )


def _group_key(stack):
    return stack.name.rstrip('0123456789')


def test_build_graph_includes_selfloop():
    graph = build_graph(_selfloop_data(), node_key_fn=_group_key)

    _assert_graph(
        graph,
        nodes=['stack-a', 'stack-b'],
        edges=[('stack-a', 'stack-a', 'export-1'), ('stack-a', 'stack-b', 'export-2')],
    )


def test_build_graph_removes_selfloop():
    graph = build_graph(_selfloop_data(), node_key_fn=_group_key, remove_selfloops=True)

    _assert_graph(graph, nodes=['stack-a', 'stack-b'], edges=[('stack-a', 'stack-b', 'export-2')])


def test_build_graph_uses_node_key_fn():
    node_key_fn = Mock(side_effect=lambda stack: f'{stack.name}-key')

    graph = build_graph(_exports(_export('export-1', 'stack-a', ['stack-b'])), node_key_fn=node_key_fn)

    _assert_graph(graph, nodes=['stack-a-key', 'stack-b-key'], edges=[('stack-a-key', 'stack-b-key', 'export-1')])
    assert node_key_fn.call_args_list == [call(Stack(name='stack-a')), call(Stack(name='stack-b'))]


def test_build_graph_merges_stacks_with_the_same_key():
    data = _exports(
        _export('export-1', 'stack-a1', ['stack-b']),
        _export('export-2', 'stack-a2', ['stack-b']),
    )

    graph = build_graph(data, node_key_fn=_group_key)

    assert graph.nodes['stack-a'] == {
        'stacks': {Stack(name='stack-a1'), Stack(name='stack-a2')},
        'exports': {'export-1': data['export-1'], 'export-2': data['export-2']},
    }
    assert graph.nodes['stack-b']['stacks'] == {Stack(name='stack-b')}
