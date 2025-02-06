from typing import List, Dict, Optional

from botocore.client import BaseClient
from botocore.exceptions import ClientError
import boto3


def parse_name_from_id(stack_id: str) -> str:
    try:
        return stack_id.split('/')[1]
    except IndexError as err:
        # log warning message
        ...
    return ''


def list_all_exports(cfn_client: Optional[BaseClient] = None) -> List[Dict]:
    if cfn_client is None:
        cfn_client = boto3.client('cloudformation')

    exports = []
    resp = cfn_client.list_exports()
    exports.extend(resp['Exports'])
    while token := resp.get('NextToken'):
        resp = cfn_client.list_exports(NextToken=token)
        exports.extend(resp['Exports'])
    return exports


def get_imports(export_name: str, cfn_client: Optional[BaseClient] = None) -> List[str]:
    if cfn_client is None:
        cfn_client = boto3.client('cloudformation')

    imports = []
    try:
        resp = cfn_client.list_imports(ExportName=export_name)
        print(resp)
        imports.extend(resp['Imports'])
        while token := resp.get('NextToken'):
            resp = cfn_client.list_imports(ExportName=export_name, NextToken=token)
            imports.extend(resp['Imports'])
    except ClientError as err:
        # todo: add logging here
        if not 'is not imported by any stack' in repr(err):
            raise err
    return imports
