from aws_cdk import Environment, Stage, Tags
from constructs import Construct
from stack.cyclic_stack_a import CyclicStackA
from stack.cyclic_stack_b import CyclicStackB


class CyclicStage(Stage):
    def __init__(self, scope: Construct, id: str, env: Environment) -> None:
        super().__init__(scope, id, env=env)
        Tags.of(self).add('cycl-e2e-group', 'cyclic')  # read back by the e2e tests
        create_cycle: str = self.node.try_get_context('create_cycle') or ''
        stack_a = CyclicStackA(
            self,
            'CyclicStackA',
            create_cycle=create_cycle.lower() == 'true',
        )
        stack_b = CyclicStackB(
            self,
            'CyclicStackB',
        )
        # B imports A's export by name (Fn.import_value), which CDK can't see, so declare it: A deploys first and
        # B is destroyed first. The import back from A to B (create_cycle) is left out, as it is the cycle under test.
        stack_b.add_dependency(stack_a)
