from aws_cdk import (
    Stack,
    aws_ec2 as ec2
)
from constructs import Construct
from infra.config import EnvironmentConfig


class NetworkStack(Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: EnvironmentConfig,
        **kwargs
        ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.vpc = ec2.Vpc(
            self, f"NetworkVPC",
            vpc_name=f"citibike-vpc-{config.env_name}",
            max_azs=2,
            nat_gateways=0,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="Isolated",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24
                ),
            ]
        )

        self.vpc.add_gateway_endpoint(
            "S3Endpoint",
            service=ec2.GatewayVpcEndpointAwsService.S3
        )
        self.vpc.add_gateway_endpoint(
            "DynamoDBEndpoint",
            service=ec2.GatewayVpcEndpointAwsService.DYNAMODB
        )
