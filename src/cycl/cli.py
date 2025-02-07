import argparse
import logging
import sys

import networkx as nx

from cycl import build_dependency_graph
from cycl.utils.log_config import configure_logging


def app() -> None:
    parser = argparse.ArgumentParser(description='Check for cross-stack import/export circular dependencies.')
    subparsers = parser.add_subparsers(dest='action', required=True)

    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument('--exit-zero', action='store_true', help='exit 0 regardless of result')
    parent_parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='ERROR',
        help='Set the logging level (default: ERROR)',
    )

    subparsers.add_parser('check', parents=[parent_parser], help='Check for cycles in AWS stack imports/exports')

    args = parser.parse_args()
    configure_logging(getattr(logging, args.log_level))

    if args.action == 'check':
        cycle_found = False
        graph = build_dependency_graph()
        cycles = nx.simple_cycles(graph)
        for cycle in cycles:
            cycle_found = True
            print(f'Cycle found between nodes: {cycle}')
        if cycle_found and not args.exit_zero:
            sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    app()
