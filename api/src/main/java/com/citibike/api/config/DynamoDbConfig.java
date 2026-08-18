package com.citibike.api.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import software.amazon.awssdk.auth.credentials.AwsBasicCredentials;
import software.amazon.awssdk.auth.credentials.StaticCredentialsProvider;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.dynamodb.DynamoDbClient;
import software.amazon.awssdk.services.dynamodb.DynamoDbClientBuilder;

import java.net.URI;

@Configuration
public class DynamoDbConfig {

    @Value("${aws.region:us-east-1}")
    private String region;

    @Value("${aws.dynamodb.endpoint-override:}")
    private String endpointOverride;

    @Value("${aws.dynamodb.access-key-id:}")
    private String accessKeyId;

    @Value("${aws.dynamodb.secret-access-key:}")
    private String secretAccessKey;

    @Bean
    public DynamoDbClient dynamoDbClient() {
        DynamoDbClientBuilder builder = DynamoDbClient.builder()
                .region(Region.of(region));

        // If running locally with an endpoint override (http://localhost:8000)
        if (endpointOverride != null && !endpointOverride.isBlank()) {
            builder.endpointOverride(URI.create(endpointOverride));
        }

        // If static dummy credentials are provided (local profile)
        if (accessKeyId != null && secretAccessKey != null) {
            builder.credentialsProvider(
                StaticCredentialsProvider.create(
                    AwsBasicCredentials.create(accessKeyId, secretAccessKey)
                )
            );
        }
        // Otherwise, AWS SDK defaults to DefaultCredentialsProvider (ECS Task Role in dev/prod)

        return builder.build();
    }
}