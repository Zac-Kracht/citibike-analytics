'''
V2 API infra using API Gateway + AWS Lambda w/ SnapStart to reduce Java cold start times
'''
from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    aws_lambda as lambda_,
    aws_ec2 as ec2,
    aws_dynamodb as dynamodb,
    aws_logs as logs,
    aws_apigatewayv2 as apigwv2,
    aws_apigatewayv2_integrations as integrations,
    aws_wafv2 as wafv2
)
from constructs import Construct
from infra.config import EnvironmentConfig
from infra.constants import (
    REMOVAL_POLICY_MAP,
    LOG_RETENTION_DAYS_MAP
)

class APIStackV2(Stack):

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

        self.api_log_group = logs.LogGroup(
            self, "LambdaAPILogGroup",
            log_group_name=f"/aws/lambda/citibike-api-{config.env_name}",
            retention=LOG_RETENTION_DAYS_MAP[config.logs_retention_days],
            removal_policy=REMOVAL_POLICY_MAP[config.removal_policy]
        )

        self.lambda_security_group = ec2.SecurityGroup(
            self, "LambdaSecurityGroup",
            vpc=vpc,
            description="Security Group for CitiBike Lambda API",
            allow_all_outbound=True
        )

        self.lambda_fn = lambda_.Function(
            self, "CitibikeApiLambda",
            function_name=f"citibike-api-lambda-{config.env_name}",
            runtime=lambda_.Runtime.JAVA_21,
            code=lambda_.Code.from_asset("../api/target/api-0.0.1-SNAPSHOT.jar"), 
            handler="com.citibike.api.StreamLambdaHandler", 
            memory_size=2048, 
            timeout=Duration.seconds(30),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
            security_groups=[self.lambda_security_group],
            log_group=self.api_log_group,
            # Enable SnapStart for published versions to eliminate cold starts
            snap_start=lambda_.SnapStartConf.ON_PUBLISHED_VERSIONS,
            environment={
                "SPRING_PROFILES_ACTIVE": config.env_name,
                "DYNAMODB_TABLE_NAME": live_station_table.table_name,
                "DYNAMO_TABLE_POLL_RATE": str(config.api_config.dynamo_poll_rate_ms)
            }
        )

        live_station_table.grant_read_data(self.lambda_fn)

        self.lambda_version = self.lambda_fn.current_version
        self.lambda_alias = lambda_.Alias(
            self, "LambdaLiveAlias",
            alias_name="live",
            version=self.lambda_version
        )

        self.http_api = apigwv2.HttpApi(
            self, "CitibikeHttpApi",
            api_name=f"citibike-api-{config.env_name}",
            cors_preflight=apigwv2.CorsPreflightOptions(
                allow_origins=config.api_config.allowed_origins,
                allow_methods=[apigwv2.CorsHttpMethod.GET],
                allow_headers=["Authorization", "Content-Type", "X-Origin-Verify"]
            )
        )

        self.lambda_integration = integrations.HttpLambdaIntegration(
            "LambdaIntegration",
            handler=self.lambda_alias
        )

        self.http_api.add_routes(
            path="/{proxy+}",
            methods=[apigwv2.HttpMethod.GET],
            integration=self.lambda_integration
        )

        if config.api_config.enable_waf:
            secret_token_reference = f"{{{{resolve:secretsmanager:{config.api_config.secret_name}:SecretString}}}}"

            self.web_acl = wafv2.CfnWebACL(
                self, "WebACL",
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
                                        search_string=secret_token_reference,
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

            # Associate WAF WebACL directly with the API Gateway stage ARN
            wafv2.CfnWebACLAssociation(
                self, f"WafAssociation",
                resource_arn=self.http_api.default_stage.stage_arn,
                web_acl_arn=self.web_acl.attr_arn
            )

        # Output the public API Gateway endpoint for your React frontend
        CfnOutput(
            self, "ApiEndpointUrl",
            value=self.http_api.url,
            description="Secure API Gateway HTTP API Endpoint URL"
        )

        