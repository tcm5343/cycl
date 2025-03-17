from __future__ import annotations

from logging import getLogger
from pathlib import Path

import boto3
import networkx as nx
from botocore.config import Config

from cycl.models.export_data import ExportData
from cycl.utils.cdk import get_exports_from_assembly

log = getLogger(__name__)


def get_graph_data(cdk_out_path: Path | None = None) -> dict[str, ExportData]:
    cdk_out_imports: dict[str, list[ExportData]] = get_exports_from_assembly(Path(cdk_out_path)) if cdk_out_path else {}
    log.info('cdk_out_imports: %s', cdk_out_imports)

    boto_config = Config(retries={'max_attempts': 10, 'mode': 'adaptive'})
    cfn_client = boto3.client('cloudformation', config=boto_config)

    log.info('getting all exports')
    exports = ExportData.get_all_exports(cfn_client=cfn_client)
    for export_name, importing_stacks in cdk_out_imports.items():
        if export_name not in exports:
            log.warning(
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


def build_graph(
    graph_data: dict[str, ExportData] | None = None,
    cdk_out_path: Path | None = None,
    # node_key: Callable[[ExportData], str] = lambda x: x.stack_name,
    nodes_to_ignore: list[str] | None = None,
    edges_to_ignore: list[list[str]] | None = None,
) -> nx.MultiDiGraph:
    nodes_to_ignore = nodes_to_ignore or []
    edges_to_ignore = edges_to_ignore or []
    graph_data = get_graph_data(cdk_out_path) if graph_data is None else graph_data

    log.info('building dependency graph from graph data')
    dep_graph: nx.MultiDiGraph = nx.MultiDiGraph()
    for export in graph_data.values():
        # export_key = node_key(export)
        if export.stack_name in nodes_to_ignore:
            continue

        edges = []
        for importing_stack in export.importing_stacks:
            # importing_key = node_key(importing_stack)
            if importing_stack.stack_name not in nodes_to_ignore:
                edge = (export.stack_name, importing_stack.stack_name)
                if list(edge) not in edges_to_ignore:
                    edges.append(edge)

        if edges:
            dep_graph.add_edges_from(ebunch_to_add=edges)
        else:
            # export key
            dep_graph.add_node(export.stack_name)
    return dep_graph
