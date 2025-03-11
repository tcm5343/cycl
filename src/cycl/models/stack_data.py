from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

import boto3
from botocore.exceptions import ClientError

if TYPE_CHECKING:
    from mypy_boto3_cloudformation import CloudFormationClient

log = getLogger(__name__)


class StackData:
    def __init__(  # noqa: PLR0913
        self,
        stack_name: str,
        stack_id: str | None = None,
        export_name: str | None = None,
        export_value: str | None = None,
        parent_id: str | None = None,
        root_id: str | None = None,
        tags: dict[str, str] | None = None,
        outputs: list[str] | None = None,
        importing_stacks: list[StackData] | None = None,
    ) -> None:
        self.stack_name = stack_name
        self.stack_id = stack_id
        self.export_name = export_name
        self.export_value = export_value
        self.parent_id = parent_id
        self.root_id = root_id
        self.tags = tags
        self.outputs = outputs or []
        self.importing_stacks = importing_stacks or []

    @classmethod
    def from_list_exports(cls, list_exports_resp: dict[str, str]) -> dict[str, StackData]:
        """Convert an AWS CloudFormation list exports response into a dictionary of export name to StackData instances.

        Args:
            list_exports_resp: A dictionary representing the list exports response,
                where each entry contains export details with keys:
                - 'ExportingStackId': The ID of the stack exporting the value.
                - 'Name': The name of the export.
                - 'Value': The exported value.

        Returns:
            A dictionary mapping export names to StackData instances,
            where each StackData object contains information about the corresponding export.
        """
        return {
            export['Name']: cls(
                stack_name=cls.parse_name_from_id(export['ExportingStackId']),
                stack_id=export['ExportingStackId'],
                export_name=export['Name'],
                export_value=export['Value'],
            )
            for export in list_exports_resp['Exports']
        }

    @classmethod
    def get_all_exports(cls, cfn_client: CloudFormationClient | None = None) -> dict[str, StackData]:
        """Retrieve all AWS CloudFormation exports and return them as a dictionary of export name to StackData instances.

        Args:
            cfn_client: A Boto3 CloudFormation client instance.
                If not provided, a new client will be created.

        Returns:
            A dictionary mapping export names to StackData instances,
            where each StackData object contains details about the corresponding export.

        Note:
            This function paginates through the AWS CloudFormation `list_exports` API to retrieve all exports.
        """
        cfn_client = cfn_client or boto3.client('cloudformation')

        exports: dict[str, StackData] = {}
        resp = cfn_client.list_exports()
        log.debug(resp)
        exports.update(StackData.from_list_exports(resp))
        while token := resp.get('NextToken'):
            resp = cfn_client.list_exports(NextToken=token)
            log.debug(resp)
            exports.update(StackData.from_list_exports(resp))
        log.debug(exports)
        return exports

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, StackData):
            return False
        return vars(self) == vars(other)

    def __hash__(self) -> int:
        return hash(tuple((key, tuple(value) if isinstance(value, list) else value) for key, value in vars(self).items()))

    def __repr__(self) -> str:
        return f'StackData(stack_name={self.stack_name!r}, export_name={self.export_name!r})'

    def get_all_imports(self, cfn_client: CloudFormationClient | None = None) -> StackData:
        """Retrieve all stacks that import the current export and update the importing_stacks attribute.

        Args:
            cfn_client: A Boto3 CloudFormation client instance. If not provided, a new client will be created.

        Returns:
            The updated instance with importing stacks added to the `importing_stacks` attribute.

        Note:
            This function paginates through the AWS CloudFormation `list_imports` API to retrieve all importing stacks.
            If the export is not imported by any stack, it logs a debug message instead of raising an error.
        """
        cfn_client = cfn_client or boto3.client('cloudformation')

        try:
            resp = cfn_client.list_imports(ExportName=self.export_name)
            log.debug(resp)
            self.importing_stacks.extend(
                [StackData(stack_name=importing_stack_name) for importing_stack_name in resp['Imports']]
            )
            while token := resp.get('NextToken'):
                resp = cfn_client.list_imports(ExportName=self.export_name, NextToken=token)
                log.debug(resp)
                self.importing_stacks.extend(
                    [StackData(stack_name=importing_stack_name) for importing_stack_name in resp['Imports']]
                )
        except ClientError as err:
            if 'is not imported by any stack' not in repr(err):
                raise
            log.debug('')  # TODO: log something helpful
        log.debug(self.importing_stacks)
        return self

    @staticmethod
    def parse_name_from_id(stack_id: str) -> str:
        """Extract the stack name from a given stack ID.

        Args:
            stack_id: The full stack ID, typically in the format
                'arn:aws:cloudformation:region:account-id:stack/stack-name/guid'.

        Returns:
            The extracted stack name, or an empty string if parsing fails.

        Note:
            Logs a warning if the stack ID format is unexpected.
        """
        try:
            return stack_id.split('/')[1]
        except IndexError:
            log.warning('Unable to parse name from stack_id: %s', stack_id)
            return ''
