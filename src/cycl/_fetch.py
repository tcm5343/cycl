from __future__ import annotations

import dataclasses
from logging import getLogger
from typing import TYPE_CHECKING

import boto3
from botocore.config import Config

from cycl._utils.cfn import describe_all_stacks, list_exports, list_importing_stacks

if TYPE_CHECKING:
    from mypy_boto3_cloudformation import CloudFormationClient

    from cycl.models import Export, Stack


log = getLogger(__name__)

_DEFAULT_CLIENT_CONFIG = Config(retries={'max_attempts': 10, 'mode': 'adaptive'})


def fetch_exports(*, cfn_client: CloudFormationClient | None = None, describe_stacks: bool = False) -> dict[str, Export]:
    """Collect every CloudFormation export in the account and region, along with the stacks importing it.

    ``ListImports`` only returns stack names, so by default an importing stack gets its ARN (``id``) only if it
    also defines an export, and ``tags`` are empty. With ``describe_stacks``, every stack gets its ARN and tags.

    This makes one ``ListImports`` call per export, so it can take a while on accounts with many exports. Fetch
    once and pass the result to :func:`build_graph` as many times as needed.

    Args:
        cfn_client: CloudFormation client used to list exports and imports. If omitted, one is created with
            ``boto3`` (standard credential chain) and adaptive retries (10 attempts). A client you pass in is
            used as is, so configure retries on it yourself to avoid throttling on accounts with many exports,
            for example ``boto3.Session(profile_name=..., region_name=...).client('cloudformation',
            config=botocore.config.Config(retries={'max_attempts': 10, 'mode': 'adaptive'}))``.
        describe_stacks: Also make a ``DescribeStacks`` call (paginated, about one call per 100 stacks), to fill in
            the ``id`` and ``tags`` of every stack. Requires the ``cloudformation:DescribeStacks``
            and ``cloudformation:ListStacks`` permissions.

    Returns:
        A mapping of export name to its :class:`~cycl.Export`.
    """
    cfn_client = cfn_client or boto3.client('cloudformation', config=_DEFAULT_CLIENT_CONFIG)

    log.info('getting all exports')
    exports = list_exports(cfn_client)

    log.info('getting imports for %s exports', len(exports))
    importing_stacks = {name: list_importing_stacks(cfn_client, name) for name in exports}

    if describe_stacks:
        log.info('describing stacks')
        stacks = describe_all_stacks(cfn_client)
    else:
        # use the ARN from ListExports for importers which also export, so equal stacks compare equal
        stacks = {export.exporting_stack.name: export.exporting_stack for export in exports.values()}

    def resolve(stack: Stack) -> Stack:
        if stack.name in stacks:
            return stacks[stack.name]
        if describe_stacks:
            log.warning('Unable to describe stack %s, it may have been deleted', stack.name)
        return stack

    for name, export in exports.items():
        if not importing_stacks[name]:
            log.warning('Export found with no import: %s from %s', name, export.exporting_stack.name)
        exports[name] = dataclasses.replace(
            export,
            exporting_stack=resolve(export.exporting_stack),
            importing_stacks=tuple(dict.fromkeys(resolve(stack) for stack in importing_stacks[name])),
        )
    return exports
