#!/usr/bin/env python3
import os

import aws_cdk as cdk

from infra.data_pipeline_stack import DataPipelineStack
from infra.config import ENVIRONMENTS


app = cdk.App()

# Read environment from the CLI flag, default to dev for local development
target_env = app.node.try_get_context("env") or "dev"
config = ENVIRONMENTS.get(target_env)

if not config:
    raise ValueError(f"Invalid environment: {target_env}. Must be 'dev' or 'prod'.")

cdk_env = cdk.Environment(
    account=os.getenv('CDK_DEFAULT_ACCOUNT'), 
    region=os.getenv('CDK_DEFAULT_REGION')
)

DataPipelineStack(
    app, 
    f"CitiBike-DataPipeline-{config.env_name}",
    config,
    env=cdk_env
)

app.synth()
