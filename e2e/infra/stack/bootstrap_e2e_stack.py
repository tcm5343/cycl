from constructs import Construct
from aws_cdk import (
    Stack,
    CfnOutput,
    aws_iam as iam,
    Environment,
)


class BootstrapE2EStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, env: Environment) -> None:
        super().__init__(scope, construct_id, stack_name='bootstrap-e2e-stack')

        github_repo_name = 'tcm5343/cycl'  # can this be dynamic

        oidc_provider = iam.OpenIdConnectProvider.from_open_id_connect_provider_arn(
            self, "GitHubOIDCProvider",
            f"arn:aws:iam::{env.account}:oidc-provider/token.actions.githubusercontent.com"
        )

        e2e_managed_policy = iam.ManagedPolicy(self, "CfnListImportsExportsPolicy",
            managed_policy_name="e2e-role-policy",
            statements=[
                iam.PolicyStatement(
                    actions=[
                        "cloudformation:ListExports",
                        "cloudformation:ListImports",
                        # "cloudformation:DescribeStacks"
                    ],
                    resources=["*"]
                )
            ],
            description="Minimum permissions needed to use all features of cycl."
        )

        role = iam.Role(self, "GithubCfnInspectorRole",
            role_name="e2e-role",
            assumed_by=iam.WebIdentityPrincipal(
                oidc_provider.open_id_connect_provider_arn,
                conditions={
                    "StringLike": {
                        "token.actions.githubusercontent.com:sub": f"repo:{github_repo_name}:ref:refs/heads/*"
                    }
                }
            ),
            description="E2E testing role, used in GH actions, to run cycl with."
        )

        role.add_managed_policy(e2e_managed_policy)
