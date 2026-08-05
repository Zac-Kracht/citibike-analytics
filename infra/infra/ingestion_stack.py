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
from config import EnvironmentConfig

class IngestionStack(Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: EnvironmentConfig,
        **kwargs
        ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        is_dev = config.env_name == "dev"
        removal_policy = RemovalPolicy.DESTROY if is_dev else RemovalPolicy.RETAIN

        if is_dev:
            bronze_lifecycle_rules = [
                s3.LifecycleRule(
                    id="DevExpireGBFSJson",
                    prefix="bronze/gbfs/",
                    expiration=Duration.days(7)
                ),
                s3.LifecycleRule(
                    id="DevExpireHistoricalCSV",
                    prefix="bronze/historical/",
                    expiration=Duration.days(30)
                ),
                s3.LifecycleRule(
                    id="DevAbortIncompleteUploads",
                    abort_incomplete_upload_after=Duration.days(1)
                ),
            ]
        else:
            bronze_lifecycle_rules = [
                s3.LifecycleRule(
                    id="ProdIntelligentTieringGBFS",
                    prefix="bronze/gbfs/",
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INTELLIGENT_TIERING,
                            transition_after=Duration.days(30)
                        )
                    ],
                    expiration=Duration.days(180)
                ),
                s3.LifecycleRule(
                    id="ProdGlacierHistoricalCSV",
                    prefix="bronze/historical/",
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                            transition_after=Duration.days(30),
                        ),
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(90),
                        ),
                    ]
                ),
                s3.LifecycleRule(
                    id="ProdAbortIncompleteUploads",
                    abort_incomplete_upload_after=Duration.days(7)
                ),
            ]

        self.bronze_bucket = s3.Bucket(
            self,
            "CitiBikeAnalyticsBronzeBucket",
            bucket_name_prefix=f"citibike-data-lake-bronze-{config.env_name}",
            bucket_namespace=s3.BucketNamespace.ACCOUNT_REGIONAL,
            removal_policy=removal_policy,
            auto_delete_objects=is_dev, 
            versioned=False,
            lifecycle_rules=bronze_lifecycle_rules
        )


