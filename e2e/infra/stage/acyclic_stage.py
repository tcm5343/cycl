from aws_cdk import Stage, Environment
from constructs import Construct

from infra.stack.acyclic_stack import AcyclicStack


class AcyclicStage(Stage):
    def __init__(self, scope: Construct, id: str, env: Environment):
        super().__init__(scope, id, env=env)

        AcyclicStack(self, "AcyclicStack")
