from aws_cdk import CfnOutput, Fn, Stack
from constructs import Construct


class CyclicStackB(Stack):
    def __init__(self, scope: Construct, construct_id: str) -> None:
        super().__init__(scope, construct_id, stack_name='cyclic-stack-b')

        imported_value = Fn.import_value('cyclic-stack-a-export-1')

        CfnOutput(self, 'ExportedValue', value=imported_value, export_name='cyclic-stack-b-export-1')
