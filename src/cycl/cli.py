import json
import logging
import sys
from logging import getLogger

import networkx as nx

from cycl import build_dependency_graph
from cycl.parser import create_parser
from cycl.utils.log_config import configure_log

log = getLogger(__name__)


def app() -> None:
    parser = create_parser()

    if len(sys.argv) == 1:
        parser.print_help()
        exit(0)

    args = parser.parse_args()
    configure_log(getattr(logging, args.log_level))

    dep_graph = build_dependency_graph(cdk_out_path=args.cdk_out, nodes_to_ignore=args.ignore_nodes)
    cycles = list(nx.simple_cycles(dep_graph))
    for cycle in cycles:
        print(f'cycle found between nodes: {cycle}')

    if args.cmd == 'check':
        if cycles and not args.exit_zero:
            sys.exit(1)
    elif args.cmd == 'topo':
        if cycles:
            log.error('graph is cyclic, topological generations can only be computed on an acyclic graph')
            sys.exit(1)
        generations = [sorted(generation) for generation in nx.topological_generations(dep_graph)]
        print(json.dumps(generations, indent=2))
    sys.exit(0)


if __name__ == '__main__':
    app()
