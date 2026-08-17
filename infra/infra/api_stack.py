from aws_cdk import (
    Stack,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_ecr_assets as ecr_assets,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_logs as logs
)
from constructs import Construct
from infra.config import EnvironmentConfig


class APIStack(Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: EnvironmentConfig,
        live_station_table: dynamodb.ITable,
        **kwargs
        ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        stack_prefix = "CitiBikeDataPipeline"