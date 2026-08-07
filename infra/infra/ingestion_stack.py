from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_logs as logs,
    aws_events as events,
    aws_events_targets as targets
)
from constructs import Construct
from infra.config import EnvironmentConfig

STORAGE_CLASS_MAP = {
    "INTELLIGENT_TIERING": s3.StorageClass.INTELLIGENT_TIERING,
    "INFREQUENT_ACCESS": s3.StorageClass.INFREQUENT_ACCESS,
    "GLACIER": s3.StorageClass.GLACIER,
}

REMOVAL_POLICY_MAP = {
    "RETAIN": RemovalPolicy.RETAIN,
    "DESTROY": RemovalPolicy.DESTROY,
}

LOG_RETENTION_DAYS_MAP = {
    "ONE_WEEK": logs.RetentionDays.ONE_WEEK,
    "ONE_MONTH": logs.RetentionDays.ONE_MONTH,
    "ONE_YEAR": logs.RetentionDays.ONE_YEAR
}

class IngestionStack(Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: EnvironmentConfig,
        **kwargs
        ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        stack_prefix = "CitiBikeAnalytics"

        bronze_lifecycle_rules = []
        for rule_cfg in config.s3_lifecycle_rules:
            transitions = [
                s3.Transition(
                    storage_class=STORAGE_CLASS_MAP[t.storage_class],
                    transition_after=Duration.days(t.transition_after_days)
                )
                for t in rule_cfg.transitions
            ]
            bronze_lifecycle_rules.append(
                s3.LifecycleRule(
                    id=rule_cfg.id,
                    prefix=rule_cfg.prefix,
                    transitions = transitions if transitions else None,
                    expiration = Duration.days(rule_cfg.expiration_days) if rule_cfg.expiration_days else None,
                    abort_incomplete_multipart_upload_after=Duration.days(rule_cfg.abort_incomplete_upload_after_days) if rule_cfg.abort_incomplete_upload_after_days else None
                )
            )

        self.bronze_bucket = s3.Bucket(
            self, f"{stack_prefix}BronzeBucket",
            bucket_name_prefix=f"citibike-data-lake-bronze-{config.env_name}",
            bucket_namespace=s3.BucketNamespace.ACCOUNT_REGIONAL,
            versioned=False,
            removal_policy=REMOVAL_POLICY_MAP[config.removal_policy],
            auto_delete_objects=config.s3_auto_delete_objects, 
            lifecycle_rules=bronze_lifecycle_rules,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True
        )

        self.ingestion_lambda_log_group = logs.LogGroup(
            self, f"{stack_prefix}IngestionLambdaLogGroup",
            log_group_name=f"/aws/lambda/citibike-ingestion-lambda-{config.env_name}",
            retention=LOG_RETENTION_DAYS_MAP[config.lambda_logs_retention_days],
            removal_policy=REMOVAL_POLICY_MAP[config.removal_policy]
        )

        self.ingestion_lambda = lambda_.Function(
            self, f"{stack_prefix}IngestionLambda",
            function_name=f"citibike-ingestion-lambda-{config.env_name}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="src.handler.lambda_handler",
            log_group=self.ingestion_lambda_log_group,
            code=lambda_.Code.from_asset(
                path="../lambda",
                exclude=[
                    ".venv",
                    ".pytest_cache",
                    "venv",
                    ".git",
                    "__pycache__",
                    "*.pyc",
                    "node_modules"
                ]
            ),
            timeout=Duration.seconds(30),
            memory_size=256,
            environment = {
                "BRONZE_BUCKET_NAME": self.bronze_bucket.bucket_name,
                "DYNAMODB_TABLE_NAME": "",
                "GBFS_DISCOVERY_URL": "https://gbfs.citibikenyc.com/gbfs/2.3/gbfs.json",
                "ENV_NAME": config.env_name,
                "OWNER_CONTACT": "zac.kracht.dev@gmail.com",
                "LANGUAGE_CODE": "en"
            }
        )

        self.bronze_bucket.grant_write(self.ingestion_lambda)

        self.bronze_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                sid="RestrictWriteToIngestionLambdaOnly",
                effect=iam.Effect.DENY,
                principals=[iam.AnyPrincipal()],
                actions=["s3:PutObject", "s3:AbortMultipartUpload"],
                resources=[f"{self.bronze_bucket.bucket_arn}/*"],
                conditions={
                    "StringNotLike": {
                        "aws:PrincipalArn": [
                            self.ingestion_lambda.role.role_arn,
                            # Allow CloudFormation/CDK deployment role to manage objects if needed
                            f"arn:aws:iam::{self.account}:role/cdk-*",
                            f"arn:aws:iam::{self.account}:root", 
                            f"arn:aws:iam::{self.account}:user/*",  
                            f"arn:aws:iam::{self.account}:role/aws-reserved/*"
                        ]
                    }
                }
            )
        )

        # self.bronze_bucket.add_to_resource_policy(
        #     iam.PolicyStatement(
        #         sid="RestrictReadToGlueJobOnly",
        #         effect=iam.Effect.DENY,
        #         principals=[iam.AnyPrincipal()],
        #         actions=["s3:GetObject", "s3:ListBucket"],
        #         resources=[data_bucket.bucket_arn, f"{data_bucket.bucket_arn}/*"],
        #         conditions={
        #             "StringNotLike": {
        #                 "aws:PrincipalArn": [
        #                     glue_job_role.role_arn,
        #                     f"arn:aws:iam::{self.account}:role/cdk-*"
        #                 ]
        #             }
        #         }
        #     )
        # )

        self.scheduled_lambda_rule = events.Rule(
            self, f"{stack_prefix}ScheduledLambdaRule",
            rule_name=f"citibike-scheduled-lambda-rules-{config.env_name}",
            schedule=events.Schedule.rate(Duration.minutes(config.lambda_poll_rate_minutes))
        )
        self.scheduled_lambda_rule.add_target(targets.LambdaFunction(self.ingestion_lambda))


