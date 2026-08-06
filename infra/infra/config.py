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
class EnvironmentConfig:
    env_name: str
    removal_policy: str
    s3_auto_delete_objects: bool
    s3_lifecycle_rules: List[LifecycleRuleConfig]

ENVIRONMENTS: Dict[str, EnvironmentConfig] = {
    "dev": EnvironmentConfig(
        env_name="dev",
        removal_policy="DESTROY",
        s3_auto_delete_objects=True,
        s3_lifecycle_rules=[
            LifecycleRuleConfig(
                id="DevExpireGBFSJson",
                prefix="bronze/gbfs/",
                expiration_days=7
            ),
            LifecycleRuleConfig(
                id="DevExpireHistoricalCSV",
                prefix="bronze/historical/",
                expiration_days=30
            ),
            LifecycleRuleConfig(
                id="DevAbortIncompleteUploads",
                abort_incomplete_upload_after_days=1
            )
        ]
    ),
    "prod": EnvironmentConfig(
        env_name="prod",
        removal_policy="RETAIN",
        s3_auto_delete_objects=False,
        s3_lifecycle_rules=[
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
                id="ProdGlacierHistoricalCSV",
                prefix="bronze/historical/",
                transitions=[
                    TransitionConfig(
                        storage_class="INFREQUENT_ACCESS",
                        transition_after_days=30
                    ),
                    TransitionConfig(
                        storage_class="GLACIER",
                        transition_after_days=90
                    ),
                ],
            ),
            LifecycleRuleConfig(
                id="ProdAbortIncompleteUploads",
                abort_incomplete_upload_after_days=7
            )
        ]
    )
}