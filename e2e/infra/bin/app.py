from aws_cdk import App, Environment
from stack.bootstrap_e2e_stack import BootstrapE2EStack
from stage.acyclic_stage import AcyclicStage
from stage.cyclic_stage import CyclicStage


def app() -> None:
    app = App()
    account_id = app.node.try_get_context('accountId')

    BootstrapE2EStack(app, 'BootstrapE2EStack', env=Environment(account=account_id, region='us-east-1'))
    AcyclicStage(app, 'AcyclicStage', env=Environment(account=account_id, region='us-east-1'))
    CyclicStage(app, 'CyclicStage', env=Environment(account=account_id, region='us-west-2'))

    app.synth()


if __name__ == '__main__':
    app()
