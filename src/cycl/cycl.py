from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from logging import getLogger
from pathlib import Path
from queue import Queue
from typing import TYPE_CHECKING

import boto3
import networkx as nx
from botocore.config import Config

from cycl.utils.cdk import get_cdk_out_imports
from cycl.utils.cfn import get_all_exports, get_all_imports, parse_name_from_id

if TYPE_CHECKING:
    from botocore.client import BaseClient

log = getLogger(__name__)


def __get_imports_mapper(export: tuple[str, dict], cfn_client: BaseClient) -> dict:
    export[1]['ExportingStackName'] = parse_name_from_id(export[1]['ExportingStackId'])
    export[1].setdefault('ImportingStackNames', []).extend(
        get_all_imports(export_name=export[1]['Name'], cfn_client=cfn_client)
    )
    return {export[0]: export[1]}


def __map_existing_exports_to_imports(exports: dict) -> dict:
    res = {}
    q = Queue()

    max_workers = 10
    boto_config = Config(
        retries={
            'max_attempts': 10,
            'mode': 'adaptive',
        },
        max_pool_connections=max_workers,
    )
    cfn_client = boto3.client('cloudformation', config=boto_config)

    for item in exports.items():
        q.put(item)

    futures = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        while not q.empty():
            futures.append(executor.submit(__get_imports_mapper, export=q.get(), cfn_client=cfn_client))

    for future in futures:
        err = future.exception()
        if err:
            log.error(err)
        else:
            res.update(future.result())
    return res


def __get_graph_data(cdk_out_path: Path | None = None) -> dict:
    """TODO: make this public and test"""
    cdk_out_imports = {}
    if cdk_out_path:
        cdk_out_imports = get_cdk_out_imports(Path(cdk_out_path))

    exports = get_all_exports()
    for export_name, importing_stack_names in cdk_out_imports.items():
        if export_name in exports:
            exports[export_name].setdefault('ImportingStackNames', []).extend(importing_stack_names)
        if export_name not in exports:
            log.warning(
                'found an export (%s) which has not been deployed yet about to be imported stack(s): (%s)',
                export_name,
                cdk_out_imports[export_name],
            )

    return __map_existing_exports_to_imports(exports=exports)


def build_dependency_graph(cdk_out_path: Path | None = None) -> nx.MultiDiGraph:
    dep_graph = nx.MultiDiGraph()
    mapped_exports = __get_graph_data(cdk_out_path)
    for export in mapped_exports.values():
        edges = [
            (export['ExportingStackName'], importing_stack_name) for importing_stack_name in export['ImportingStackNames']
        ]
        if edges:
            dep_graph.add_edges_from(ebunch_to_add=edges)
        else:
            log.info('Export found with no import: %s', export['ExportingStackName'])
            dep_graph.add_node(export['ExportingStackName'])
    return dep_graph
