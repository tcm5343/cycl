import argparse
import json
import logging
import pathlib
import sys
from logging import getLogger

import networkx as nx

from cycl import build_graph
from cycl.utils.log_config import configure_log

log = getLogger(__name__)


# def get_node_key_function(node_key: str, missing_tag: str = 'ignore') -> Callable[[NodeData], str]:
#     if node_key.startswith("tag:"):
#         tag_name = node_key.split(":", 1)[1]

#         if missing_tag == 'error':
#             return lambda x: x.tags[tag_name]  # strict mode

#         default_value = f"Unknown-{tag_name}" if missing_tag == 'default' else x.stack_name
#         return lambda x: x.tags.get(tag_name, default_value)

#     node_key_map = {
#         'stack_name': lambda x: x.stack_name,
#         'export_name': lambda x: x.export_name or 'NoExport',
#         'parent_id': lambda x: x.parent_id or 'NoParent',
#     }

#     return node_key_map.get(node_key, lambda x: x.stack_name)


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='cycl', description='Check circular dependencies between imports and exports.')
    sp = parser.add_subparsers(dest='cmd', required=True)

    check_p = sp.add_parser('check', help='Check for cycles between AWS stack imports and exports.')
    check_p.add_argument('--exit-zero', action='store_true', help='Exit zero regardless of cyclic check result.')

    topo_p = sp.add_parser('topo', help='Find topological generations, if dependencies are acyclic')

    # global options
    for p in [check_p, topo_p]:
        p.add_argument(
            '--log-level',
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            default='INFO',
            help='Sets the logging level.',
        )
        p.add_argument(
            '--cdk-out',
            type=pathlib.Path,
            help='EXPERIMENTAL: Path to cdk.out/, where the cdk synthesizes the cloud assembly output.',
        )
        p.add_argument(
            '--ignore-nodes',
            nargs='+',
            default=[],
            type=str,
            help=(
                "List of nodes to to ignore when building the graph. Don't repeat ``--ignore-nodes`` if you "
                'have multiple nodes (ex. ``--ignore-nodes v1 v2``).'
            ),
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
        # p.add_argument(  # TODO
        #     '--node-key',
        #     type=str,
        #     choices=['stack_name', 'export_name', 'parent_id', 'tag:Environment'],
        #     default='stack_name',
        #     help='Specify which NodeData attribute to use as the graph node identifier.'
        # )
        # parser.add_argument(
        #     '--missing-tag',
        #     choices=['ignore', 'error', 'default'],
        #     default='ignore',
        #     help='How to handle missing tags: "ignore" (fallback to stack name), "error" (raise),
        # or "default" (custom value).'
        # )
    return parser


def app() -> None:
    parser = create_parser()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()
    configure_log(getattr(logging, args.log_level))

    dep_graph = build_graph(
        cdk_out_path=args.cdk_out,
        nodes_to_ignore=args.ignore_nodes,
        edges_to_ignore=args.ignore_edge,
    )

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
