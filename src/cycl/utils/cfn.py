from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

import boto3
from botocore.exceptions import ClientError

if TYPE_CHECKING:
    from botocore.client import BaseClient

log = getLogger(__name__)


def parse_name_from_id(stack_id: str) -> str:
    try:
        return stack_id.split('/')[1]
    except IndexError:
        log.warning('unable to parse name from stack_id: %s', stack_id)
    return ''


def get_all_exports(cfn_client: BaseClient | None = None) -> dict:
    if cfn_client is None:
        cfn_client = boto3.client('cloudformation')

    exports = {}
    resp = cfn_client.list_exports()
    log.debug(resp)
    exports.update({export['Name']: export for export in resp['Exports']})
    while token := resp.get('NextToken'):
        resp = cfn_client.list_exports(NextToken=token)
        log.debug(resp)
        exports.update({export['Name']: export for export in resp['Exports']})
    log.debug(exports)
    return exports


def get_all_imports(export_name: str, cfn_client: BaseClient | None = None) -> list[str]:
    if cfn_client is None:
        cfn_client = boto3.client('cloudformation')

    imports = []
    try:
        resp = cfn_client.list_imports(ExportName=export_name)
        log.debug(resp)
        imports.extend(resp['Imports'])
        while token := resp.get('NextToken'):
            resp = cfn_client.list_imports(ExportName=export_name, NextToken=token)
            log.debug(resp)
            imports.extend(resp['Imports'])
    except ClientError as err:
        if 'is not imported by any stack' not in repr(err):
            raise
        log.debug('')
    log.debug(imports)
    return imports
