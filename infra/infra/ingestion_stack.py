from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    aws_lambda as lambda_,
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
            lifecycle_rules=bronze_lifecycle_rules
        )

        self.ingestion_lambda = lambda_.Function(
            self, f"{stack_prefix}IngestionLambda",
            function_name=f"citibike-ingestion-lambda-{config.env_name}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="src.handler.lambda_handler",
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


