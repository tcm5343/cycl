#!/usr/bin/env python3
from aws_cdk import App, Environment

from infra.stage.acyclic_stage import AcyclicStage
from infra.stage.cyclic_stage import CyclicStage

ACCOUNT_NUMBER = '929185124050'


def app():
    app = App()
    AcyclicStage(
        app, "AcyclicStage",
        env=Environment(account=ACCOUNT_NUMBER, region='us-east-1')
    )
    CyclicStage(
        app, "CyclicStage",
        env=Environment(account=ACCOUNT_NUMBER, region='us-west-2')
    )
    app.synth()


if __name__ == '__main__':
    app()
