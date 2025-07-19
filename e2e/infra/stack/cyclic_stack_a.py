from aws_cdk import CfnOutput, Fn, Stack
from constructs import Construct


class CyclicStackA(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        create_cycle: bool = False,
    ) -> None:
        super().__init__(scope, construct_id, stack_name='cyclic-stack-a')

        CfnOutput(self, 'InitialExportedValue', value='static-value-or-reference', export_name='cyclic-stack-a-export-1')

        if create_cycle:
            CfnOutput(
                self,
                'CyclicExportedValue',
                value=Fn.import_value('cyclic-stack-b-export-1'),
                export_name='cyclic-stack-a-export-2',
            )
