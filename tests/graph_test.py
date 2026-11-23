from unittest.mock import Mock, call

import networkx as nx
import pytest

from cycl import Export, Stack, build_graph, merge_graphs


def _stack(name, account='000'):
    return Stack(name=name, id=f'arn:{account}:{name}')


def _export(name, exporter, importers=(), account='000'):
    return Export(
        name=name,
        value=f'{name}-value',
        exporting_stack=_stack(exporter, account),
        importing_stacks=tuple(_stack(importer, account) for importer in importers),
    )


def _exports(*exports):
    return {export.name: export for export in exports}


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

    assert graph.nodes['stack-a'] == {'stacks': {_stack('stack-a')}, 'exports': {'export-1': data['export-1']}}
    assert graph.nodes['stack-b'] == {'stacks': {_stack('stack-b')}, 'exports': {'export-2': data['export-2']}}
    assert graph.nodes['stack-c'] == {'stacks': {_stack('stack-c')}, 'exports': {}}


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
    assert node_key_fn.call_args_list == [call(_stack('stack-a')), call(_stack('stack-b'))]


def test_build_graph_merges_stacks_with_the_same_key():
    data = _exports(
        _export('export-1', 'stack-a1', ['stack-b']),
        _export('export-2', 'stack-a2', ['stack-b']),
    )

    graph = build_graph(data, node_key_fn=_group_key)

    assert graph.nodes['stack-a'] == {
        'stacks': {_stack('stack-a1'), _stack('stack-a2')},
        'exports': {'export-1': data['export-1'], 'export-2': data['export-2']},
    }
    assert graph.nodes['stack-b']['stacks'] == {_stack('stack-b')}


# merge_graphs


def test_merge_graphs_returns_empty_graph():
    assert nx.number_of_nodes(merge_graphs({})) == 0


def test_merge_graphs_keeps_same_named_exports_and_stacks_from_each_source():
    dev = _exports(_export('export-1', 'stack-a', ['stack-b'], account='dev'))
    prod = _exports(_export('export-1', 'stack-a', ['stack-b'], account='prod'))

    merged = merge_graphs({'dev': build_graph(dev), 'prod': build_graph(prod)})

    _assert_graph(
        merged,
        nodes=['stack-a', 'stack-b'],
        edges=[('stack-a', 'stack-b', ('dev', 'export-1')), ('stack-a', 'stack-b', ('prod', 'export-1'))],
    )
    assert merged.nodes['stack-a'] == {
        'stacks': {_stack('stack-a', 'dev'), _stack('stack-a', 'prod')},
        'exports': {('dev', 'export-1'): dev['export-1'], ('prod', 'export-1'): prod['export-1']},
    }
    assert merged.edges['stack-a', 'stack-b', ('prod', 'export-1')]['export'] == prod['export-1']


def test_merge_graphs_finds_cycles_across_sources():
    dev = build_graph(_exports(_export('export-1', 'stack-a', ['stack-b'], account='dev')))
    prod = build_graph(_exports(_export('export-2', 'stack-b', ['stack-a'], account='prod')))

    assert nx.is_directed_acyclic_graph(dev)
    assert nx.is_directed_acyclic_graph(prod)
    assert len(list(nx.simple_cycles(merge_graphs({'dev': dev, 'prod': prod})))) == 1


def test_merge_graphs_keeps_sources_separate_when_node_keys_include_them():
    def scoped(source):
        return lambda stack: (source, stack.name)

    dev = build_graph(_exports(_export('export-1', 'stack-a', ['stack-b'], account='dev')), node_key_fn=scoped('dev'))
    prod = build_graph(_exports(_export('export-2', 'stack-b', ['stack-a'], account='prod')), node_key_fn=scoped('prod'))

    merged = merge_graphs({'dev': dev, 'prod': prod})

    assert nx.number_of_nodes(merged) == 4
    assert nx.is_directed_acyclic_graph(merged)
