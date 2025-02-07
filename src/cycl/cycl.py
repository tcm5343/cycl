from logging import getLogger

import networkx as nx

from cycl.utils.cfn import get_all_exports, get_all_imports, parse_name_from_id

log = getLogger(__name__)


def build_dependency_graph() -> nx.MultiDiGraph:
    dep_graph = nx.MultiDiGraph()

    exports = get_all_exports()
    for export in exports:
        export['ExportingStackName'] = parse_name_from_id(export['ExportingStackId'])
        export['ImportingStackNames'] = get_all_imports(export_name=export['Name'])
        edges = [
            (export['ExportingStackName'], importing_stack_name) for importing_stack_name in export['ImportingStackNames']
        ]
        if edges:
            dep_graph.add_edges_from(ebunch_to_add=edges)
        else:
            log.info('Export found with no import: %s', export['ExportingStackName'])
            dep_graph.add_node(export['ExportingStackName'])
    return dep_graph
