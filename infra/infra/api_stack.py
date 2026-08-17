from aws_cdk import (
    Stack,
    Duration,
    aws_ecs as ecs,
    aws_ec2 as ec2,
    aws_ecs_patterns as ecs_patterns,
    aws_ecr_assets as ecr_assets,
    aws_wafv2 as wafv2,
    aws_dynamodb as dynamodb,
    aws_secretsmanager as secretsmanager,
    aws_iam as iam,
    aws_logs as logs
)
from constructs import Construct
from infra.config import EnvironmentConfig

from infra.constants import (
    REMOVAL_POLICY_MAP,
    LOG_RETENTION_DAYS_MAP
)


class APIStack(Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: EnvironmentConfig,
        live_station_table: dynamodb.ITable,
        vpc: ec2.IVpc,
        **kwargs
        ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.cluster = ecs.Cluster(
            self, f"ECSCluster",
            cluster_name=f"citibike-ecs-cluster-{config.env_name}",
            vpc=vpc
        )

        self.api_log_group = logs.LogGroup(
            self, f"ECSLogGroup",
            log_group_name=f"/ecs/citibike-api-{config.env_name}",
            retention=LOG_RETENTION_DAYS_MAP[config.logs_retention_days],
            removal_policy=REMOVAL_POLICY_MAP[config.removal_policy]
        )

        self.fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, f"FargateService",
            cluster=self.cluster,
            service_name=f"citibike-api-service-{config.env_name}",
            cpu=config.fargate_config.cpu,
            memory_limit_mib=config.fargate_config.memory_limit_mib,
            desired_count=config.fargate_config.desired_count,
            assign_public_ip=False,
            public_load_balancer=config.api_config.public_alb,
            task_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_asset("../backend"),
                container_port=8080,
                log_driver=ecs.LogDriver.aws_logs(
                    stream_prefix="citibike-api",
                    log_group=self.api_log_group
                ),
                environment={
                    "SPRING_PROFILES_ACTIVE": config.env_name,
                    "DYNAMODB_TABLE_NAME": live_station_table.table_name,
                    "AWS_REGION": self.region
                }
            )
        )

        # Use SPOT instances in dev for cost savings
        if config.api_config.use_fargate_spot:
            cfn_service = self.fargate_service.service.node.default_child
            cfn_service.capacity_provider_strategy = [
                {
                    "capacityProvider": "FARGATE_SPOT",
                    "weight": 1
                }
            ]

        # Limit dev traffic to local device
        if not config.api_config.public_alb or config.env_name == "dev":
            self.fargate_service.load_balancer.connections.security_groups[0].add_ingress_rule(
                peer=ec2.Peer.ipv4(config.api_config.allowed_cidrs[0]),
                connection=ec2.Port.tcp(80),
                description="Allow local development machine only"
            )

        live_station_table.grant_read_data(self.fargate_service.task_definition.task_role)

        self.fargate_service.target_group.configure_health_check(
            path="/actuator/health",
            port="8080",
            healthy_http_codes="200",
            interval=Duration.seconds(30),
            timeout=Duration.seconds(5)
        )

        if config.api_config.enable_waf:
            origin_secret = secretsmanager.Secret.from_secret_name_v2(
                self, f"APIOriginSecret", config.api_config.secret_name
            )
            secret_token = origin_secret.secret_value.unsafe_unwrap()

            self.web_acl = wafv2.CfnWebACL(
                self, f"WebACL",
                default_action=wafv2.CfnWebACL.DefaultActionProperty(allow={}),
                scope="REGIONAL",
                visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                    cloud_watch_metrics_enabled=True,
                    metric_name=f"CitiBikeApiWafMetric-{config.env_name}",
                    sampled_requests_enabled=True
                ),
                rules=[
                    # Custom Header Verification Rule (Blocks non-frontend traffic)
                    wafv2.CfnWebACL.RuleProperty(
                        name="RequireFrontendCustomHeader",
                        priority=0,
                        action=wafv2.CfnWebACL.RuleActionProperty(block={}),
                        statement=wafv2.CfnWebACL.StatementProperty(
                            not_statement=wafv2.CfnWebACL.StatementProperty(
                                statement=wafv2.CfnWebACL.StatementProperty(
                                    byte_match_statement=wafv2.CfnWebACL.ByteMatchStatementProperty(
                                        search_string=secret_token,
                                        field_to_match=wafv2.CfnWebACL.FieldToMatchProperty(
                                            single_header={"name": config.api_config.secret_header_name.lower()}
                                        ),
                                        text_transformations=[
                                            wafv2.CfnWebACL.TextTransformationProperty(
                                                priority=0,
                                                type="NONE"
                                            )
                                        ],
                                        positional_constraint="EXACTLY"
                                    )
                                )
                            )
                        ),
                        visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                            cloud_watch_metrics_enabled=True,
                            metric_name="RequireFrontendCustomHeaderMetric",
                            sampled_requests_enabled=True
                        )
                    ),
                    # Rate Limiting: Max 100 requests per 5 minutes per IP address
                    wafv2.CfnWebACL.RuleProperty(
                        name="RateLimitRule",
                        priority=1,
                        action=wafv2.CfnWebACL.RuleActionProperty(block={}),
                        statement=wafv2.CfnWebACL.StatementProperty(
                            rate_based_statement=wafv2.CfnWebACL.RateBasedStatementProperty(
                                limit=100,
                                aggregate_key_type="IP"
                            )
                        ),
                        visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                            cloud_watch_metrics_enabled=True,
                            metric_name="RateLimitMetric",
                            sampled_requests_enabled=True
                        )
                    ),
                    # AWS Managed Common Rule Set
                    wafv2.CfnWebACL.RuleProperty(
                        name="AWSCommonRules",
                        priority=2,
                        override_action=wafv2.CfnWebACL.OverrideActionProperty(none={}),
                        statement=wafv2.CfnWebACL.StatementProperty(
                            managed_rule_group_statement=wafv2.CfnWebACL.ManagedRuleGroupStatementProperty(
                                vendor_name="AWS",
                                name="AWSManagedRulesCommonRuleSet"
                            )
                        ),
                        visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                            cloud_watch_metrics_enabled=True,
                            metric_name="AWSCommonRulesMetric",
                            sampled_requests_enabled=True
                        )
                    )
                ]
            )

            wafv2.CfnWebACLAssociation(
                self, f"WafAssociation",
                resource_arn=self.fargate_service.load_balancer.load_balancer_arn,
                web_acl_arn=self.web_acl.attr_arn
            )

