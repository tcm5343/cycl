from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

import boto3
from botocore.exceptions import ClientError

from cycl.utils.cfn import parse_name_from_id

if TYPE_CHECKING:
    from mypy_boto3_cloudformation import CloudFormationClient
    from mypy_boto3_cloudformation.type_defs import ListExportsOutputTypeDef

log = getLogger(__name__)


class NodeData:
    """Data collected to be used in graph creation."""

    def __init__(
        self,
        stack_name: str,
        stack_id: str | None = None,
        export_name: str | None = None,
        export_value: str | None = None,
        importing_stacks: list[NodeData] | None = None,
        # parent_id: str | None = None,
        # root_id: str | None = None,
        # tags: dict[str, str] | None = None,
        # outputs: list[str] | None = None,
    ) -> None:
        self.stack_name = stack_name
        self.stack_id = stack_id
        self.export_name = export_name
        self.export_value = export_value
        self.importing_stacks = importing_stacks or []
        # self.parent_id = parent_id
        # self.root_id = root_id
        # self.tags = tags
        # self.outputs = outputs or []

    @classmethod
    def from_list_exports(cls, list_exports_resp: ListExportsOutputTypeDef) -> dict[str, NodeData]:
        """Convert an AWS CloudFormation list exports response into a dictionary of export name to NodeData instances.

        Args:
            list_exports_resp: A dictionary representing the list exports response,
                where each entry contains export details with keys:
                - 'ExportingStackId': The ID of the stack exporting the value.
                - 'Name': The name of the export.
                - 'Value': The exported value.

        Returns:
            A dictionary mapping export names to NodeData instances,
            where each NodeData object contains information about the corresponding export.
        """
        return {
            export['Name']: cls(
                stack_name=parse_name_from_id(export['ExportingStackId']),
                stack_id=export['ExportingStackId'],
                export_name=export['Name'],
                export_value=export['Value'],
            )
            for export in list_exports_resp['Exports']
        }

    @classmethod
    def get_all_exports(cls, cfn_client: CloudFormationClient | None = None) -> dict[str, NodeData]:
        """Retrieve all AWS CloudFormation exports and return them as a dictionary of export name to NodeData instances.

        Args:
            cfn_client: A Boto3 CloudFormation client instance.
                If not provided, a new client will be created.

        Returns:
            A dictionary mapping export names to NodeData instances,
            where each NodeData object contains details about the corresponding export.

        Note:
            This function paginates through the AWS CloudFormation `list_exports` API to retrieve all exports.
        """
        cfn_client = cfn_client or boto3.client('cloudformation')

        exports: dict[str, NodeData] = {}
        resp = cfn_client.list_exports()
        log.debug(resp)
        exports.update(NodeData.from_list_exports(resp))
        while token := resp.get('NextToken'):
            resp = cfn_client.list_exports(NextToken=token)
            log.debug(resp)
            exports.update(NodeData.from_list_exports(resp))
        log.debug(exports)
        return exports

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, NodeData):
            return False
        return vars(self) == vars(other)

    def __hash__(self) -> int:
        return hash(tuple((key, tuple(value) if isinstance(value, list) else value) for key, value in vars(self).items()))

    def __repr__(self) -> str:
        return f'NodeData(stack_name={self.stack_name!r}, export_name={self.export_name!r})'

    def get_all_imports(self, cfn_client: CloudFormationClient | None = None) -> NodeData:
        """Retrieve all stacks that import the current export and update the importing_stacks attribute.

        Args:
            cfn_client: A Boto3 CloudFormation client instance. If not provided, a new client will be created.

        Returns:
            The updated instance with importing stacks added to the `importing_stacks` attribute.

        Note:
            This function paginates through the AWS CloudFormation `list_imports` API to retrieve all importing stacks.
            If the export is not imported by any stack, it logs a debug message instead of raising an error.
        """
        if self.export_name:
            cfn_client = cfn_client or boto3.client('cloudformation')

            try:
                resp = cfn_client.list_imports(ExportName=self.export_name)
                log.debug(resp)
                self.importing_stacks.extend(
                    [NodeData(stack_name=importing_stack_name) for importing_stack_name in resp['Imports']]
                )
                while token := resp.get('NextToken'):
                    resp = cfn_client.list_imports(ExportName=self.export_name, NextToken=token)
                    log.debug(resp)
                    self.importing_stacks.extend(
                        [NodeData(stack_name=importing_stack_name) for importing_stack_name in resp['Imports']]
                    )
            except ClientError as err:
                if 'is not imported by any stack' not in repr(err):
                    raise
                log.debug('')  # TODO: refine msg
            log.debug(self.importing_stacks)
        else:
            warning_msg = (
                f'export_name not defined for {type(self).__name__}, which probably means {self.stack_name} '
                'imports an export but does not export any'
            )
            log.warning(warning_msg)
        return self
