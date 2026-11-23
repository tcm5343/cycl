"""Command line interface for cycl.

Exit codes:
    0: No cycles found (or ``--exit-zero`` was passed to ``check``).
    1: An error occurred, e.g. invalid usage or an AWS error. Any unexpected exception also exits 1, so 1 is
       never mistaken for a result.
    2: A cycle was found.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from logging import getLogger
from typing import TYPE_CHECKING, NoReturn

import networkx as nx

from cycl._core import build_graph, fetch_exports
from cycl._utils.log_config import configure_log

if TYPE_CHECKING:
    from collections.abc import Hashable

log = getLogger(__name__)

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_CYCLE_FOUND = 2


class _ArgumentParser(argparse.ArgumentParser):
    """Exit 1 on usage errors (argparse defaults to 2), so 2 only ever means a cycle was found.

    Sub-parsers inherit this class, since ``add_subparsers`` defaults to the parent parser's class.
    """

    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        self.exit(EXIT_ERROR, f'{self.prog}: error: {message}\n')


def create_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(prog='cycl', description='Check circular dependencies between imports and exports.')
    sp = parser.add_subparsers(dest='cmd', required=True)

    check_p = sp.add_parser('check', help='Check for cycles between AWS stack imports and exports.')
    check_p.add_argument('--exit-zero', action='store_true', help='Exit zero even if a cycle is found.')

    topo_p = sp.add_parser('topo', help='Find topological generations, if dependencies are acyclic.')

    # options shared by every sub-command
    for p in [check_p, topo_p]:
        p.add_argument(
            '--log-level',
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            default='INFO',
            help='Sets the logging level. Logs are written to stderr.',
        )
        p.add_argument(
            '--format',
            choices=['text', 'json'],
            default='text',
            help='Output format written to stdout.',
        )
        p.add_argument(
            '--ignore-node',
            default=[],
            action='append',
            metavar='NODE',
            help='Specify a node to ignore. ``--ignore-node NODE`` must be repeated for each node provided.',
        )
        p.add_argument(
            '--ignore-edge',
            nargs=2,
            default=[],
            action='append',
            metavar=('u', 'v'),
            help=(
                'Specify an edge to ignore by providing two nodes delimited by a space. ``--ignore-edge u v`` must be '
                'repeated for each edge provided.'
            ),
        )
    return parser


def _print_cycles_text(cycles: list[list[Hashable]]) -> None:
    for cycle in cycles:
        print(f'cycle found between nodes: {cycle}')


def _check(cycles: list[list[Hashable]], args: argparse.Namespace) -> int:
    if args.format == 'json':
        print(json.dumps({'cycles': cycles}, indent=2))
    else:
        _print_cycles_text(cycles)

    if cycles and not args.exit_zero:
        return EXIT_CYCLE_FOUND
    return EXIT_OK


def _topo(dep_graph: nx.MultiDiGraph, cycles: list[list[Hashable]], args: argparse.Namespace) -> int:
    generations = None if cycles else [sorted(generation) for generation in nx.topological_generations(dep_graph)]

    if args.format == 'json':
        print(json.dumps({'cycles': cycles, 'generations': generations}, indent=2))
    elif generations is None:
        _print_cycles_text(cycles)
    else:
        for generation in generations:
            print(' '.join(map(str, generation)))

    if cycles:
        log.error('graph is cyclic, topological generations can only be computed on an acyclic graph')
        return EXIT_CYCLE_FOUND
    return EXIT_OK


def app() -> None:
    parser = create_parser()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(EXIT_OK)

    args = parser.parse_args()
    configure_log(getattr(logging, args.log_level))

    dep_graph = build_graph(
        fetch_exports(),
        ignore_nodes=args.ignore_node,
        ignore_edges=[tuple(edge) for edge in args.ignore_edge],
    )
    cycles = list(nx.simple_cycles(dep_graph))

    if args.cmd == 'check':
        sys.exit(_check(cycles, args))
    sys.exit(_topo(dep_graph, cycles, args))


if __name__ == '__main__':
    app()
