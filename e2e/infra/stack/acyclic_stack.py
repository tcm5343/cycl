from constructs import Construct
from aws_cdk import (
    Stack,
    CfnOutput
)


class AcyclicStack(Stack):

    def __init__(self, scope: Construct, construct_id: str) -> None:
        super().__init__(scope, construct_id, stack_name='acyclic-stack')

        CfnOutput(
            self, "ExportedValue",
            value="static-value-or-reference",
            export_name="MyNoopExport"
        )
