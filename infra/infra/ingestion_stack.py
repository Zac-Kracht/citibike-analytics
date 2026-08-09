from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    aws_lambda as lambda_,
    aws_glue as glue,
    aws_iam as iam,
    aws_logs as logs,
    aws_events as events,
    aws_events_targets as targets,
    aws_s3_assets as s3_assets,
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

        # S3 Data Lake

        s3_lifecycle_rules = []
        for rule_cfg in config.s3_config.lifecycle_rules:
            transitions = [
                s3.Transition(
                    storage_class=STORAGE_CLASS_MAP[t.storage_class],
                    transition_after=Duration.days(t.transition_after_days)
                )
                for t in rule_cfg.transitions
            ]
            s3_lifecycle_rules.append(
                s3.LifecycleRule(
                    id=rule_cfg.id,
                    prefix=rule_cfg.prefix,
                    transitions = transitions if transitions else None,
                    expiration = Duration.days(rule_cfg.expiration_days) if rule_cfg.expiration_days else None,
                    abort_incomplete_multipart_upload_after=Duration.days(rule_cfg.abort_incomplete_upload_after_days) if rule_cfg.abort_incomplete_upload_after_days else None
                )
            )

        self.s3_bucket = s3.Bucket(
            self, f"{stack_prefix}DataLakeBucket",
            bucket_name_prefix=f"citibike-analytics-data-lake-{config.env_name}",
            bucket_namespace=s3.BucketNamespace.ACCOUNT_REGIONAL,
            versioned=False,
            removal_policy=REMOVAL_POLICY_MAP[config.removal_policy],
            auto_delete_objects=config.s3_config.auto_delete_objects, 
            lifecycle_rules=s3_lifecycle_rules,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True
        )

        # Ingestion Lambda

        self.ingestion_lambda_log_group = logs.LogGroup(
            self, f"{stack_prefix}IngestionLambdaLogGroup",
            log_group_name=f"/aws/lambda/citibike-ingestion-lambda-{config.env_name}",
            retention=LOG_RETENTION_DAYS_MAP[config.lambda_config.logs_retention_days],
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
                "DATA_LAKE_BUCKET_NAME": self.s3_bucket.bucket_name,
                "DYNAMODB_TABLE_NAME": "",
                "GBFS_DISCOVERY_URL": "https://gbfs.citibikenyc.com/gbfs/2.3/gbfs.json",
                "ENV_NAME": config.env_name,
                "OWNER_CONTACT": "zac.kracht.dev@gmail.com",
                "LANGUAGE_CODE": "en"
            }
        )

        self.s3_bucket.grant_write(self.ingestion_lambda)

        self.scheduled_lambda_rule = events.Rule(
            self, f"{stack_prefix}ScheduledLambdaRule",
            rule_name=f"citibike-scheduled-lambda-rule-{config.env_name}",
            schedule=events.Schedule.rate(Duration.minutes(config.lambda_config.poll_rate_minutes))
        )
        self.scheduled_lambda_rule.add_target(targets.LambdaFunction(self.ingestion_lambda))

        # Glue Jobs

        self.glue_role = iam.Role(
            self, f"{stack_prefix}GlueRole",
            role_name=f"citibike-analytics-glue-service-role-{config.env_name}",
            assumed_by=iam.ServicePrincipal("glue.amazonaws.com")
        )
        self.glue_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSGlueServiceRole"))

        self.s3_bucket.grant_read_write(self.glue_role)

        ## Bronze -> Silver

        self.gbfs_script_asset = s3_assets.Asset(
            self, f"{stack_prefix}GBFSBronzeToSilverScriptAsset",
            path="../etl//jobs/gbfs_bronze_to_silver.py"
        )
        self.gbfs_glue_job = glue.CfnJob(
            self, f"{stack_prefix}GBFSBronzeToSilverGlueJob",
            name=f"citibike-etl-gbfs-bronze-to-silver-{config.env_name}",
            role=self.glue_role.role_arn,
            glue_version="4.0",
            worker_types="G.1X",
            number_of_workers=2,
            execution_class=config.glue_config.execution_class,
            command=glue.CfnJob.JobCommandProperty(
                name="glueetl",
                script_location=f"s3://{self.gbfs_script_asset.s3_bucket_name}/{self.gbfs_script_asset.s3_object_key}",
                python_version="3"
            ),
            default_arguments={
                "--job-bookmark-option": "job-bookmark-enable",
                "--enable-metrics": "true",
                "--enable-continuous-cloudwatch-log": "true",
                "--DATA_LAKE_BUCKET": self.s3_bucket.bucket_name,
                "--ENV_NAME": config.env_name
            }
        )

        self.trips_script_asset = s3_assets.Asset(
            self, f"{stack_prefix}TripsBronzeToSilverScriptAsset",
            path="../etl//jobs/trips_bronze_to_silver.py"
        )
        self.trips_glue_job = glue.CfnJob(
            self, f"{stack_prefix}TripsBronzeToSilverGlueJob",
            name=f"citibike-etl-trips-bronze-to-silver-{config.env_name}",
            role=self.glue_role.role_arn,
            glue_version="4.0",
            worker_types="G.1X",
            number_of_workers=4,
            execution_class=config.glue_config.execution_class,
            command=glue.CfnJob.JobCommandProperty(
                name="glueetl",
                script_location=f"s3://{self.trips_script_asset.s3_bucket_name}/{self.trips_script_asset.s3_object_key}",
                python_version="3"
            ),
            default_arguments={
                "--job-bookmark-option": "job-bookmark-enable",
                "--enable-metrics": "true",
                "--enable-continuous-cloudwatch-log": "true",
                "--DATA_LAKE_BUCKET": self.s3_bucket.bucket_name,
                "--ENV_NAME": config.env_name
            }
        )

        # S3 Access

        self.s3_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                sid="RestrictWriteAccess",
                effect=iam.Effect.DENY,
                principals=[iam.AnyPrincipal()],
                actions=["s3:PutObject", "s3:AbortMultipartUpload"],
                resources=[f"{self.s3_bucket.bucket_arn}/*"],
                conditions={
                    "StringNotLike": {
                        "aws:PrincipalArn": [
                            self.ingestion_lambda.role.role_arn,
                            self.glue_role.role_arn,
                            f"arn:aws:iam::{self.account}:role/cdk-*",
                            f"arn:aws:iam::{self.account}:root", 
                            f"arn:aws:iam::{self.account}:user/*",  
                            f"arn:aws:iam::{self.account}:role/aws-reserved/*"
                        ]
                    }
                }
            )
        )

        self.s3_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                sid="RestrictReadAccess",
                effect=iam.Effect.DENY,
                principals=[iam.AnyPrincipal()],
                actions=["s3:GetObject", "s3:ListBucket"],
                resources=[f"{self.s3_bucket.bucket_arn}/*"],
                conditions={
                    "StringNotLike": {
                        "aws:PrincipalArn": [
                            self.glue_role.role_arn,
                            f"arn:aws:iam::{self.account}:role/cdk-*",
                            f"arn:aws:iam::{self.account}:root", 
                            f"arn:aws:iam::{self.account}:user/*",  
                            f"arn:aws:iam::{self.account}:role/aws-reserved/*"
                        ]
                    }
                }
            )
        )


