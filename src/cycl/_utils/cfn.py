from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

from botocore.exceptions import ClientError

from cycl.models import Export, Stack

if TYPE_CHECKING:
    from mypy_boto3_cloudformation import CloudFormationClient

log = getLogger(__name__)


def parse_name_from_id(stack_id: str) -> str:
    """Extract the stack name from a given stack ID.

    Args:
        stack_id: The full stack ID, typically in the format
            'arn:aws:cloudformation:region:account-id:stack/stack-name/guid'.

    Returns:
        The extracted stack name, or an empty string if parsing fails.
    """
    try:
        return stack_id.split('/')[1]
    except IndexError:
        log.warning('Unable to parse stack_name from stack_id: %s', stack_id)
        return ''


def list_exports(cfn_client: CloudFormationClient) -> dict[str, Export]:
    """Return every export in the account and region, keyed by export name, without importing stacks."""
    exports: dict[str, Export] = {}
    for page in cfn_client.get_paginator('list_exports').paginate():
        log.debug(page)
        for export in page['Exports']:
            exports[export['Name']] = Export(
                name=export['Name'],
                value=export['Value'],
                exporting_stack=Stack(name=parse_name_from_id(export['ExportingStackId']), id=export['ExportingStackId']),
            )
    return exports


def describe_all_stacks(cfn_client: CloudFormationClient) -> dict[str, Stack]:
    """Return every stack in the account and region, with its ARN and tags, keyed by stack name."""
    stacks: dict[str, Stack] = {}
    for page in cfn_client.get_paginator('describe_stacks').paginate():
        log.debug(page)
        for stack in page['Stacks']:
            stacks[stack['StackName']] = Stack(
                name=stack['StackName'],
                id=stack['StackId'],
                tags={tag['Key']: tag['Value'] for tag in stack.get('Tags', [])},
            )
    return stacks


def list_importing_stacks(cfn_client: CloudFormationClient, export_name: str) -> list[Stack]:
    """Return the stacks importing the given export, or an empty list if it is not imported."""
    stacks: list[Stack] = []
    try:
        for page in cfn_client.get_paginator('list_imports').paginate(ExportName=export_name):
            log.debug(page)
            stacks.extend(Stack(name=stack_name) for stack_name in page['Imports'])
    except ClientError as err:
        if 'is not imported by any stack' not in str(err):
            raise
        log.debug('export %s is not imported by any stack', export_name)
    return stacks
