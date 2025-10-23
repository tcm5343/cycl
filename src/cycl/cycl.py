from __future__ import annotations

from logging import getLogger
from pathlib import Path
from typing import TYPE_CHECKING, Callable

import boto3
import networkx as nx
from botocore.config import Config
from botocore.session import Session

from cycl.models import NodeData
from cycl.utils.cdk import get_exports_from_assembly

if TYPE_CHECKING:
    from collections.abc import Hashable


log = getLogger(__name__)


def get_graph_data(
    cdk_out_path: Path | None = None,
    aws_session: Session | None = None,
    aws_profile_name: str | None = None,
) -> dict[str, NodeData]:
    cdk_out_imports: dict[str, list[NodeData]] = (
        get_exports_from_assembly(Path(cdk_out_path)) if cdk_out_path is not None else {}
    )
    log.info('cdk_out_imports: %s', cdk_out_imports)

    # this logic should move to a module
    # profile and session should not be able to be provided
    boto_config = Config(retries={'max_attempts': 10, 'mode': 'adaptive'})
    if aws_session:
        cfn_client = aws_session.client('cloudformation', config=boto_config)  # type: ignore[attr-defined]
    elif aws_profile_name:
        cfn_client = Session(profile_name=aws_profile_name).client('cloudformation', config=boto_config)  # type: ignore[attr-defined,call-arg]
    else:
        cfn_client = boto3.client('cloudformation', config=boto_config)

    log.info('getting all exports')
    exports = NodeData.get_all_exports(cfn_client=cfn_client)
    for export_name, importing_stacks in cdk_out_imports.items():
        if export_name not in exports:
            log.debug(
                'found an export (%s) which has not been deployed yet about to be imported stack(s): (%s)',
                export_name,
                importing_stacks,
            )

    log.info('getting imports for %s exports', len(exports))
    for export in exports.values():
        if export.export_name:  # TODO: i think this is a given, maybe enforce at object level, add unit test
            export.get_all_imports(cfn_client=cfn_client)
            export.importing_stacks += cdk_out_imports.get(export.export_name, [])  # TODO: should we convert to method?
        if len(export.importing_stacks) == 0:
            log.warning('Export found with no import: %s from %s', export.export_name, export.stack_name)
    return exports


def __add_node_data(graph: nx.MultiDiGraph, key: Hashable, data: NodeData) -> None:
    if key not in graph:
        graph.add_node(key, node_data={data})
        return

    node_data: set[NodeData] = graph.nodes[key].setdefault('node_data', set())
    node_data.add(data)


def build_graph(  # noqa: PLR0913
    graph_data: dict[str, NodeData] | None = None,
    cdk_out_path: Path | None = None,
    node_key_fn: Callable[[NodeData], Hashable] = lambda x: x.stack_name,
    nodes_to_ignore: list[str] | None = None,
    edges_to_ignore: list[list[str]] | None = None,
    aws_session: Session | None = None,
    aws_profile_name: str | None = None,
    *,
    remove_selfloops: bool = False,
) -> nx.MultiDiGraph:
    nodes_to_ignore = nodes_to_ignore or []
    edges_to_ignore = edges_to_ignore or []
    graph_data = (
        get_graph_data(cdk_out_path=cdk_out_path, aws_session=aws_session, aws_profile_name=aws_profile_name)
        if graph_data is None
        else graph_data
    )

    log.info('building dependency graph from graph data')
    dep_graph: nx.MultiDiGraph = nx.MultiDiGraph()

    for export in graph_data.values():
        export_key = node_key_fn(export)
        if export_key in nodes_to_ignore:
            continue

        __add_node_data(dep_graph, export_key, export)

        for importing_stack in export.importing_stacks:
            importing_key = node_key_fn(importing_stack)
            if importing_key not in nodes_to_ignore:
                edge = (export_key, importing_key)
                if list(edge) not in edges_to_ignore:
                    dep_graph.add_edge(*edge)
                    __add_node_data(dep_graph, importing_key, importing_stack)

    if remove_selfloops:
        dep_graph.remove_edges_from(nx.selfloop_edges(dep_graph))

    return dep_graph
