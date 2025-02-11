from __future__ import annotations

from logging import getLogger
from pathlib import Path

import boto3
import networkx as nx
from botocore.config import Config

from cycl.utils.cdk import get_cdk_out_imports
from cycl.utils.cfn import get_all_exports, get_all_imports, parse_name_from_id

log = getLogger(__name__)


def get_dependency_graph_data(cdk_out_path: Path | None = None) -> dict:
    cdk_out_imports = {}
    if cdk_out_path:
        cdk_out_imports = get_cdk_out_imports(Path(cdk_out_path))

    boto_config = Config(
        retries={
            'max_attempts': 10,
            'mode': 'adaptive',
        }
    )
    cfn_client = boto3.client('cloudformation', config=boto_config)

    exports = get_all_exports(cfn_client=cfn_client)
    for export_name in cdk_out_imports:
        if export_name not in exports:
            log.warning(
                'found an export (%s) which has not been deployed yet about to be imported stack(s): (%s)',
                export_name,
                cdk_out_imports[export_name],
            )

    for export in exports.values():
        export['ExportingStackName'] = parse_name_from_id(export['ExportingStackId'])
        export['ImportingStackNames'] = get_all_imports(export_name=export['Name'], cfn_client=cfn_client)
        export.setdefault('ImportingStackNames', []).extend(cdk_out_imports.get(export['Name'], []))
        if len(export['ImportingStackNames']) == 0:
            log.info('Export found with no import: %s from %s', export['Name'], export['ExportingStackName'])
    return exports


def build_dependency_graph(cdk_out_path: Path | None = None) -> nx.MultiDiGraph:
    dep_graph = nx.MultiDiGraph()
    graph_data = get_dependency_graph_data(cdk_out_path)

    for export in graph_data.values():
        edges = [
            (export['ExportingStackName'], importing_stack_name) for importing_stack_name in export['ImportingStackNames']
        ]
        if edges:
            dep_graph.add_edges_from(ebunch_to_add=edges)
        else:
            dep_graph.add_node(export['ExportingStackName'])
    return dep_graph
