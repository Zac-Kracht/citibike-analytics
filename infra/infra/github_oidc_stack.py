from aws_cdk import (
    Stack,
    aws_iam as iam,
)
from constructs import Construct

class GitHubOIDCStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, github_repo: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Register GitHub as an OpenID Connect identity provider in AWS
        github_provider = iam.OpenIdConnectProvider(
            self, "GitHubProvider",
            url="https://token.actions.githubusercontent.com",
            client_ids=["sts.amazonaws.com"]
        )

        # Create the IAM role that GitHub Actions will assume
        github_role = iam.Role(
            self, "GitHubActionsDevDeployRole",
            role_name="GitHubActionsDevDeployRole",
            assumed_by=iam.FederatedPrincipal(
                github_provider.open_id_connect_provider_arn,
                conditions={
                    "StringEquals": {
                        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
                    },
                    "StringLike": {
                        "token.actions.githubusercontent.com:sub": f"repo:{github_repo}:ref:refs/heads/main"
                    }
                },
                assume_role_action="sts:AssumeRoleWithWebIdentity"
            )
        )

        # Grant permissions for CDK deployments 
        github_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AdministratorAccess")
        )