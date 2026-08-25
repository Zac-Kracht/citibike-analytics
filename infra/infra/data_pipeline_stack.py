from aws_cdk import (
    Stack,
    Duration,
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
from infra.constants import (
    STORAGE_CLASS_MAP,
    REMOVAL_POLICY_MAP,
    LOG_RETENTION_DAYS_MAP
)


class DataPipelineStack(Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: EnvironmentConfig,
        **kwargs
        ) -> None:
        super().__init__(scope, construct_id, **kwargs)

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
            self, f"S3DataLakeBucket",
            bucket_name_prefix=f"citibike-analytics-data-lake-{config.env_name}",
            bucket_namespace=s3.BucketNamespace.ACCOUNT_REGIONAL,
            versioned=False,
            removal_policy=REMOVAL_POLICY_MAP[config.removal_policy],
            auto_delete_objects=config.s3_config.auto_delete_objects, 
            lifecycle_rules=s3_lifecycle_rules,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            event_bridge_enabled=True
        )

        # DynamoDB

        self.live_station_status_table = dynamodb.Table(
            self, f"LiveStationStatusDynamoTable",
            table_name=f"citibike-live-station-status-{config.env_name}",
            partition_key=dynamodb.Attribute(
                name="station_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=REMOVAL_POLICY_MAP[config.removal_policy],
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
            point_in_time_recovery=config.dynamo_config.point_in_time_recovery,
            deletion_protection=config.dynamo_config.deletion_protection
        )

        # Ingestion Lambda

        self.ingestion_lambda_log_group = logs.LogGroup(
            self, f"IngestionLambdaLogGroup",
            log_group_name=f"/aws/lambda/citibike-ingestion-lambda-{config.env_name}",
            retention=LOG_RETENTION_DAYS_MAP[config.logs_retention_days],
            removal_policy=REMOVAL_POLICY_MAP[config.removal_policy]
        )

        self.ingestion_lambda = lambda_.Function(
            self, f"IngestionLambda",
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
            timeout=Duration.seconds(120),
            memory_size=2048,
            environment = {
                "DATA_LAKE_BUCKET_NAME": self.s3_bucket.bucket_name,
                "DYNAMODB_TABLE_NAME": self.live_station_status_table.table_name,
                "GBFS_DISCOVERY_URL": "https://gbfs.citibikenyc.com/gbfs/2.3/gbfs.json",
                "ENV_NAME": config.env_name,
                "OWNER_CONTACT": "zac.kracht.dev@gmail.com",
                "LANGUAGE_CODE": "en"
            }
        )

        self.s3_bucket.grant_write(self.ingestion_lambda)
        self.live_station_status_table.grant_write_data(self.ingestion_lambda)

        ## Lambda triggers

        self.scheduled_lambda_status_rule = events.Rule(
            self, f"ScheduledLambdaStatusRule",
            rule_name=f"citibike-scheduled-lambda-status-rule-{config.env_name}",
            schedule=events.Schedule.rate(Duration.minutes(config.lambda_config.status_poll_rate_minutes))
        )
        self.scheduled_lambda_status_rule.add_target(
            targets.LambdaFunction(
                self.ingestion_lambda,
                event=events.RuleTargetInput.from_object({"poll_type": "status"})
            )
        )

        self.scheduled_lambda_info_rule = events.Rule(
            self, f"ScheduledLambdaInfoRule",
            rule_name=f"citibike-scheduled-lambda-info-rule-{config.env_name}",
            schedule=events.Schedule.cron(hour="12", minute="0")
        )
        self.scheduled_lambda_info_rule.add_target(
            targets.LambdaFunction(
                self.ingestion_lambda,
                event=events.RuleTargetInput.from_object({"poll_type": "info"})
            )
        )

        self.scheduled_lambda_trips_rule = events.Rule(
            self, f"ScheduledLambdaTripsRule",
            rule_name=f"citibike-scheduled-lambda-trips-rule-{config.env_name}",
            schedule=events.Schedule.cron(day="15", hour="6", minute="0")
        )
        self.scheduled_lambda_trips_rule.add_target(
            targets.LambdaFunction(
                self.ingestion_lambda,
                event=events.RuleTargetInput.from_object({"poll_type": "trips"})
            )
        )

        # Glue Jobs

        self.glue_role = iam.Role(
            self, f"GlueJobRole",
            role_name=f"citibike-analytics-glue-service-role-{config.env_name}",
            assumed_by=iam.ServicePrincipal("glue.amazonaws.com")
        )
        self.glue_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSGlueServiceRole"))

        self.s3_bucket.grant_read_write(self.glue_role)

        ## Bronze -> Silver

        ### GBFS 

        self.gbfs_script_asset = s3_assets.Asset(
            self, f"GBFSBronzeToSilverScriptAsset",
            path="../etl/jobs/gbfs_bronze_to_silver.py"
        )
        self.gbfs_script_asset.grant_read(self.glue_role)

        self.gbfs_glue_job = glue.CfnJob(
            self, f"GBFSBronzeToSilverGlueJob",
            name=f"citibike-etl-gbfs-bronze-to-silver-{config.env_name}",
            role=self.glue_role.role_arn,
            glue_version="4.0",
            worker_type="G.1X",
            number_of_workers=2,
            timeout=15,
            max_retries=config.glue_config.max_retries,
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
                "--ENV_NAME": config.env_name,
                "--DATA_TO_PROCESS": "ALL"
            }
        )

        self.gbfs_hourly_trigger = glue.CfnTrigger(
            self, f"GBFSHourlyTrigger",
            name=f"citibike-etl-gbfs-hourly-trigger-{config.env_name}",
            type="SCHEDULED",
            schedule="cron(5 * * * ? *)", # Every hour at 5 past the hour
            start_on_creation=True,
            actions=[
                glue.CfnTrigger.ActionProperty(
                    job_name=self.gbfs_glue_job.name
                )
            ]
        )

        ### Trips

        self.trips_script_asset = s3_assets.Asset(
            self, f"TripsBronzeToSilverScriptAsset",
            path="../etl/jobs/trips_bronze_to_silver.py"
        )
        self.trips_script_asset.grant_read(self.glue_role)

        self.trips_glue_job = glue.CfnJob(
            self, f"TripsBronzeToSilverGlueJob",
            name=f"citibike-etl-trips-bronze-to-silver-{config.env_name}",
            role=self.glue_role.role_arn,
            glue_version="4.0",
            worker_type="G.1X",
            number_of_workers=4,
            timeout=15,
            max_retries=config.glue_config.max_retries,
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

        self.bronze_trips_event_rule = events.Rule(
            self, f"BronzeTripsEventRule",
            event_pattern=events.EventPattern(
                source=["aws.s3"],
                detail_type=["Object Created"],
                detail={
                    "bucket": {"name": [self.s3_bucket.bucket_name]},
                    "object": {
                        "key": [
                            {"wildcard": "bronze/trips/*_SUCCESS"}
                        ]
                    }
                }
            )
        )
        self.bronze_trips_event_rule.add_target(
            targets.AwsApi(
                service="Glue",
                action="startJobRun",
                parameters={"JobName": self.trips_glue_job.name}
            )
        )
