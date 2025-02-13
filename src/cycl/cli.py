import argparse
import json
import logging
import pathlib
import sys
from logging import getLogger

import networkx as nx

from cycl import build_dependency_graph
from cycl.utils.log_config import configure_log

log = getLogger(__name__)


def app() -> None:
    parser = argparse.ArgumentParser(prog='cycl', description='Check for cross-stack import/export circular dependencies.')
    sp = parser.add_subparsers(dest='cmd', required=True)

    check_p = sp.add_parser('check', help='Check for cycles between stacks in AWS stack imports/exports')
    check_p.add_argument('--exit-zero', action='store_true', help='Exit 0 regardless of result of cycle check')

    topo_p = sp.add_parser('topo', help='Find topological generations if dependencies are acyclic')

    # global options
    for p in [check_p, topo_p]:
        p.add_argument(
            '--log-level',
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            default='WARNING',
            help='Set the logging level (default: WARNING)',
        )
        # p.add_argument(
        #     "--platform",
        #     choices=["AWS"],
        #     default='AWS',
        #     help="Cloud platform to interact with",
        # )
        p.add_argument(
            '--cdk-out',
            type=pathlib.Path,
            help='Path to cdk.out, where stacks are CDK synthesized to CFN templates',
        )
        p.add_argument(
            '-in',
            '--ignore-nodes',
            nargs='+',
            default=[],
            type=str,
            help='List of nodes to ignore when building the graph (ex. --ignore-nodes s1 s2 ...)',
        )
        # p.add_argument(
        #     '-q', "--quiet",
        #     type=pathlib.Path,
        #     action='store_true',
        #     help="Suppress output",
        # )

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

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
