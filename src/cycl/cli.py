import argparse
import logging
import pathlib
import sys
from logging import getLogger

import networkx as nx

from cycl import build_dependency_graph
from cycl.utils.log_config import configure_log

log = getLogger(__name__)


def app() -> None:
    parser = argparse.ArgumentParser(description='Check for cross-stack import/export circular dependencies.')
    subparsers = parser.add_subparsers(dest='action', required=True)

    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument('--exit-zero', action='store_true', help='exit 0 regardless of result')
    parent_parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='WARNING',
        help='set the logging level (default: WARNING)',
    )
    parent_parser.add_argument(
        '--cdk-out',
        type=pathlib.Path,
        help='path to cdk.out, where stacks are CDK synthesized to CFN templates',
    )

    subparsers.add_parser('check', parents=[parent_parser], help='Check for cycles in AWS stack imports/exports')

    args = parser.parse_args()
    configure_log(getattr(logging, args.log_level))
    log.info(args)

    if args.action == 'check':
        cycle_found = False
        graph = build_dependency_graph(cdk_out_path=args.cdk_out)
        cycles = nx.simple_cycles(graph)
        for cycle in cycles:
            cycle_found = True
            print(f'cycle found between nodes: {cycle}')
        if cycle_found and not args.exit_zero:
            sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    app()
