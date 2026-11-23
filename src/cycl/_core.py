from __future__ import annotations

import dataclasses
from logging import getLogger
from operator import attrgetter
from typing import TYPE_CHECKING

import boto3
import networkx as nx
from botocore.config import Config

from cycl._utils.cfn import list_exports, list_importing_stacks

if TYPE_CHECKING:
    from collections.abc import Callable, Collection, Hashable, Mapping

    from mypy_boto3_cloudformation import CloudFormationClient

    from cycl.models import Export, Stack


log = getLogger(__name__)

_DEFAULT_CLIENT_CONFIG = Config(retries={'max_attempts': 10, 'mode': 'adaptive'})


def fetch_exports(*, cfn_client: CloudFormationClient | None = None) -> dict[str, Export]:
    """Collect every CloudFormation export in the account and region, along with the stacks importing it.

    This makes one ``ListImports`` call per export, so it can take a while on accounts with many exports. Fetch
    once and pass the result to :func:`build_graph` as many times as needed.

    Args:
        cfn_client: CloudFormation client used to list exports and imports. If omitted, one is created with
            ``boto3`` (standard credential chain) and adaptive retries. To use a specific profile or region,
            pass ``boto3.Session(profile_name=..., region_name=...).client('cloudformation')``.

    Returns:
        A mapping of export name to its :class:`~cycl.Export`.
    """
    cfn_client = cfn_client or boto3.client('cloudformation', config=_DEFAULT_CLIENT_CONFIG)

    log.info('getting all exports')
    exports = list_exports(cfn_client)

    log.info('getting imports for %s exports', len(exports))
    for name, export in exports.items():
        importing_stacks = list_importing_stacks(cfn_client, name)
        if not importing_stacks:
            log.warning('Export found with no import: %s from %s', name, export.exporting_stack.name)
        exports[name] = dataclasses.replace(export, importing_stacks=tuple(dict.fromkeys(importing_stacks)))
    return exports


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
