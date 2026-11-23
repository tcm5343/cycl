from __future__ import annotations

from logging import getLogger
from operator import attrgetter
from typing import TYPE_CHECKING

import networkx as nx

if TYPE_CHECKING:
    from collections.abc import Callable, Collection, Hashable, Mapping

    from cycl.models import Export, Stack


log = getLogger(__name__)


def _add_stack(graph: nx.MultiDiGraph, key: Hashable, stack: Stack) -> None:
    if key not in graph:
        graph.add_node(key, stacks=set(), exports={})
    graph.nodes[key]['stacks'].add(stack)


def build_graph(
    exports: Mapping[str, Export],
    *,
    node_key_fn: Callable[[Stack], Hashable] = attrgetter('name'),
    ignore_nodes: Collection[Hashable] = (),
    ignore_edges: Collection[tuple[Hashable, Hashable]] = (),
    remove_selfloops: bool = False,
) -> nx.MultiDiGraph:
    """Build a directed graph of stack dependencies, where an edge points from the exporting to the importing node.

    Args:
        exports: Result of :func:`fetch_exports`.
        node_key_fn: Function mapping a :class:`~cycl.Stack` to its node key in the graph. It is called for
            every exporting and importing stack and must return a hashable value. Defaults to the stack name.

            Stacks that map to the same key are merged into one node, whose ``stacks`` attribute holds all of
            them. This lets you look for cycles between groups of stacks, such as applications or environments,
            rather than between individual stacks. Dependencies between stacks in the same group become self
            loops, see ``remove_selfloops``.

            Node keys are what ``ignore_nodes``, ``ignore_edges`` and the resulting cycles refer to. For
            example, to group stacks by the prefix before the first ``-``::

                build_graph(exports, node_key_fn=lambda stack: stack.name.split('-')[0])

            or to group stacks by a tag::

                build_graph(exports, node_key_fn=lambda stack: stack.tags.get('github-repo', stack.name))

        ignore_nodes: Node keys to leave out of the graph.
        ignore_edges: Edges, as ``(exporter, importer)`` node key pairs, to leave out of the graph.
        remove_selfloops: Remove edges where a node depends on itself, which only happens when ``node_key_fn``
            merges an exporting stack and one of its importers into the same node.

    Returns:
        A :class:`networkx.MultiDiGraph`. Each node has a ``stacks`` attribute (``set[Stack]``) and an
        ``exports`` attribute (``dict[str, Export]``, the exports defined by the node's stacks). Each edge is
        keyed by the export name and has an ``export`` attribute (:class:`~cycl.Export`).
    """
    ignored_nodes = set(ignore_nodes)
    ignored_edges = {tuple(edge) for edge in ignore_edges}

    log.info('building dependency graph from graph data')
    dep_graph: nx.MultiDiGraph = nx.MultiDiGraph()

    for export in exports.values():
        export_key = node_key_fn(export.exporting_stack)
        if export_key in ignored_nodes:
            continue

        _add_stack(dep_graph, export_key, export.exporting_stack)
        dep_graph.nodes[export_key]['exports'][export.name] = export

        for importing_stack in export.importing_stacks:
            importing_key = node_key_fn(importing_stack)
            if importing_key in ignored_nodes or (export_key, importing_key) in ignored_edges:
                continue
            _add_stack(dep_graph, importing_key, importing_stack)
            dep_graph.add_edge(export_key, importing_key, key=export.name, export=export)

    if remove_selfloops:
        # types-networkx does not model MultiDiGraph (u, v, key) edges
        dep_graph.remove_edges_from(list(nx.selfloop_edges(dep_graph, keys=True)))  # type: ignore[arg-type]

    return dep_graph


def merge_graphs(graphs: Mapping[Hashable, nx.MultiDiGraph]) -> nx.MultiDiGraph:
    """Merge graphs built from different accounts or regions into one graph.

    Nodes with the same key in several graphs become one node, so the node keys decide what is merged. With the
    default ``node_key_fn`` (stack name), unrelated stacks that share a name across accounts would be merged, so
    build each graph with a ``node_key_fn`` that is meaningful across accounts, such as a tag, or that includes
    the source.

    Export names are only unique within an account and region, so in the merged graph edges are keyed by
    ``(source, export name)``, as are the entries of each node's ``exports``. A node's ``stacks`` is the union
    of its stacks in every graph. Fetch with ``describe_stacks=True`` to tell those stacks apart: otherwise stacks
    which only import have no ``id``, so same named ones from different sources are equal and kept once.

    Args:
        graphs: Graphs from :func:`build_graph`, keyed by a hashable label for their source, such as the
            account ID or an ``(account, region)`` pair.

    Returns:
        A :class:`networkx.MultiDiGraph` with the same node and edge attributes as :func:`build_graph`.
    """
    merged: nx.MultiDiGraph = nx.MultiDiGraph()
    for source, graph in graphs.items():
        for node, data in graph.nodes(data=True):
            if node not in merged:
                merged.add_node(node, stacks=set(), exports={})
            merged.nodes[node]['stacks'].update(data['stacks'])
            merged.nodes[node]['exports'].update(
                {(source, export_name): export for export_name, export in data['exports'].items()}
            )
        for u, v, key, data in graph.edges(keys=True, data=True):
            merged.add_edge(u, v, key=(source, key), **data)
    return merged
