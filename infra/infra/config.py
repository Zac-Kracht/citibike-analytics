import os

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class TransitionConfig:
    storage_class: str  # "INTELLIGENT_TIERING", "INFREQUENT_ACCESS", "GLACIER"
    transition_after_days: int

@dataclass
class LifecycleRuleConfig:
    id: str
    prefix: Optional[str] = None
    transitions: List[TransitionConfig] = field(default_factory=list)
    expiration_days: Optional[int] = None
    abort_incomplete_upload_after_days: Optional[int] = None

@dataclass
class S3Config:
    auto_delete_objects: bool
    lifecycle_rules: List[LifecycleRuleConfig]

@dataclass
class LambdaConfig:
    status_poll_rate_minutes: int

@dataclass
class GlueConfig:
    execution_class: str
    max_retries: int

@dataclass
class DynamoConfig:
    deletion_protection: bool
    point_in_time_recovery: bool

@dataclass
class FargateConfig:
    cpu: int
    memory_limit_mib: int
    desired_count: int

@dataclass
class APIConfig:
    public_alb: bool
    enable_waf: bool
    use_fargate_spot: bool
    secret_header_name: str
    secret_name: str
    dynamo_poll_rate_ms: int

@dataclass
class EnvironmentConfig:
    env_name: str
    removal_policy: str
    logs_retention_days: str
    s3_config: S3Config
    lambda_config: LambdaConfig
    glue_config: GlueConfig
    dynamo_config: DynamoConfig
    fargate_config: FargateConfig
    api_config: APIConfig
    

ENVIRONMENTS: Dict[str, EnvironmentConfig] = {
    "dev": EnvironmentConfig(
        env_name="dev",
        removal_policy="DESTROY",
        logs_retention_days="THREE_DAYS",
        s3_config = S3Config(
            auto_delete_objects=False,
            lifecycle_rules=[
                LifecycleRuleConfig(
                    id="DevBronzeData",
                    prefix="bronze/",
                    expiration_days=7
                ),
                LifecycleRuleConfig(
                    id="DevSilverData",
                    prefix="silver/",
                    expiration_days=14
                ),
                LifecycleRuleConfig(
                    id="DevAbortIncompleteUploads",
                    abort_incomplete_upload_after_days=1
                )
            ]
        ),
        lambda_config=LambdaConfig(
            status_poll_rate_minutes=30
        ),
        glue_config=GlueConfig(
            execution_class="FLEX",
            max_retries=0
        ),
        dynamo_config=DynamoConfig(
            deletion_protection=False,
            point_in_time_recovery=False
        ),
        fargate_config=FargateConfig(
            cpu=256,
            memory_limit_mib=512,
            desired_count=1
        ),
        api_config=APIConfig(
            public_alb=False,
            enable_waf=False,
            use_fargate_spot=True,
            secret_header_name="",
            secret_name="",
            dynamo_poll_rate_ms=1800000
        )
    ),
    "prod": EnvironmentConfig(
        env_name="prod",
        removal_policy="RETAIN",
        logs_retention_days="ONE_MONTH",
        s3_config=S3Config(
            auto_delete_objects=False,
            lifecycle_rules=[
                LifecycleRuleConfig(
                    id="ProdBronzeGBFS",
                    prefix="bronze/gbfs/",
                    transitions=[
                        TransitionConfig(
                            storage_class="INTELLIGENT_TIERING",
                            transition_after_days=30
                        )
                    ],
                    expiration_days=180
                ),
                LifecycleRuleConfig(
                    id="ProdBronzeTrips",
                    prefix="bronze/trips/",
                    transitions=[
                        TransitionConfig(
                            storage_class="INFREQUENT_ACCESS",
                            transition_after_days=30
                        ),
                        TransitionConfig(
                            storage_class="GLACIER",
                            transition_after_days=90
                        )
                    ]
                ),
                LifecycleRuleConfig(
                    id="ProdSilverData",
                    prefix="silver/",
                    transitions=[
                        TransitionConfig(
                            storage_class="GLACIER_INSTANT_RETRIEVAL",
                            transition_after_days=30
                        )
                    ],
                    expiration_days=365
                ),
                LifecycleRuleConfig(
                    id="ProdAbortIncompleteUploads",
                    abort_incomplete_upload_after_days=7
                ),
            ]
        ),
        lambda_config=LambdaConfig(
            status_poll_rate_minutes=3
        ),
        glue_config=GlueConfig(
            execution_class="STANDARD",
            max_retries=2
        ),
        dynamo_config=DynamoConfig(
            deletion_protection=True,
            point_in_time_recovery=True
        ),
        fargate_config=FargateConfig(
            cpu=256,
            memory_limit_mib=512,
            desired_count=1
        ),
        api_config=APIConfig(
            public_alb=True,
            enable_waf=True,
            use_fargate_spot=False,
            secret_header_name="X-Origin-Verify",
            secret_name="citibike/prod/origin-header-secret",
            dynamo_poll_rate_ms=180000
        )
    )
}