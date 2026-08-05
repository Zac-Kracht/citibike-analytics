from dataclasses import dataclass
from typing import Dict

@dataclass
class EnvironmentConfig:
    env_name: str

ENVIRONMENTS: Dict[str, EnvironmentConfig] = {
    "dev": EnvironmentConfig(
        env_name="dev"
    ),
    "prod": EnvironmentConfig(
        env_name="prod"
    )
}