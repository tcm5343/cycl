import argparse
import pathlib


def create_parser() -> argparse.ArgumentParser:
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
    return parser
