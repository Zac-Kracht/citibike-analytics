from aws_cdk import (
    RemovalPolicy,
    aws_s3 as s3,
    aws_logs as logs
)

STORAGE_CLASS_MAP = {
    "INTELLIGENT_TIERING": s3.StorageClass.INTELLIGENT_TIERING,
    "INFREQUENT_ACCESS": s3.StorageClass.INFREQUENT_ACCESS,
    "GLACIER": s3.StorageClass.GLACIER,
    "GLACIER_INSTANT_RETRIEVAL": s3.StorageClass.GLACIER_INSTANT_RETRIEVAL
}

REMOVAL_POLICY_MAP = {
    "RETAIN": RemovalPolicy.RETAIN,
    "DESTROY": RemovalPolicy.DESTROY,
}

LOG_RETENTION_DAYS_MAP = {
    "THREE_DAYS": logs.RetentionDays.THREE_DAYS,
    "ONE_WEEK": logs.RetentionDays.ONE_WEEK,
    "ONE_MONTH": logs.RetentionDays.ONE_MONTH,
    "ONE_YEAR": logs.RetentionDays.ONE_YEAR
}