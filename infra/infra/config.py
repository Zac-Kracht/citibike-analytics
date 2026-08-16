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
    logs_retention_days: str

@dataclass
class GlueConfig:
    execution_class: str
    max_retries: int

@dataclass
class DynamoConfig:
    deletion_protection: bool
    point_in_time_recovery: bool

@dataclass
class EnvironmentConfig:
    env_name: str
    removal_policy: str
    s3_config: S3Config
    lambda_config: LambdaConfig
    glue_config: GlueConfig
    dynamo_config: DynamoConfig
    

ENVIRONMENTS: Dict[str, EnvironmentConfig] = {
    "dev": EnvironmentConfig(
        env_name="dev",
        removal_policy="DESTROY",
        s3_config = S3Config(
            auto_delete_objects=True,
            lifecycle_rules=[
                LifecycleRuleConfig(
                    id="DevExpireGBFSJson",
                    prefix="bronze/gbfs/",
                    expiration_days=7
                ),
                LifecycleRuleConfig(
                    id="DevAbortIncompleteUploads",
                    abort_incomplete_upload_after_days=1
                )
            ]
        ),
        lambda_config=LambdaConfig(
            status_poll_rate_minutes=10,
            logs_retention_days="ONE_WEEK"
        ),
        glue_config=GlueConfig(
            execution_class="FLEX",
            max_retries=0
        ),
        dynamo_config=DynamoConfig(
            deletion_protection=False,
            point_in_time_recovery=False
        )
    ),
    "prod": EnvironmentConfig(
        env_name="prod",
        removal_policy="RETAIN",
        s3_config=S3Config(
            auto_delete_objects=False,
            lifecycle_rules=[
                LifecycleRuleConfig(
                    id="ProdIntelligentTieringGBFS",
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
                    id="ProdAbortIncompleteUploads",
                    abort_incomplete_upload_after_days=7
                )
            ]
        ),
        lambda_config=LambdaConfig(
            status_poll_rate_minutes=3,
            logs_retention_days="ONE_MONTH"
        ),
        glue_config=GlueConfig(
            execution_class="STANDARD",
            max_retries=2
        ),
        dynamo_config=DynamoConfig(
            deletion_protection=True,
            point_in_time_recovery=True
        )
    )
}