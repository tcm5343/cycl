from aws_cdk import Environment, Stage
from constructs import Construct
from stack.acyclic_stack import AcyclicStack


class AcyclicStage(Stage):
    def __init__(self, scope: Construct, id: str, env: Environment) -> None:
        super().__init__(scope, id, env=env)

        AcyclicStack(self, 'AcyclicStack')
