from aws_cdk import Stage, Environment
from constructs import Construct

from stack.cyclic_stack_a import CyclicStackA
from stack.cyclic_stack_b import CyclicStackB


class CyclicStage(Stage):
    def __init__(self, scope: Construct, id: str, env: Environment):
        super().__init__(scope, id, env=env)
        create_cycle: str = self.node.try_get_context("create_cycle") or ''

        CyclicStackA(
            self, "CyclicStackA",
            create_cycle=create_cycle.lower() == 'true',
        )

        CyclicStackB(
            self, 'CyclicStackB',
        )
