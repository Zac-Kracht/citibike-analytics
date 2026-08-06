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
            self,
            "CitiBikeAnalyticsBronzeBucket",
            bucket_name_prefix=f"citibike-data-lake-bronze-{config.env_name}",
            bucket_namespace=s3.BucketNamespace.ACCOUNT_REGIONAL,
            versioned=False,
            removal_policy=REMOVAL_POLICY_MAP[config.removal_policy],
            auto_delete_objects=config.s3_auto_delete_objects, 
            lifecycle_rules=bronze_lifecycle_rules
        )


