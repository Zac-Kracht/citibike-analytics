from src.config import Config

def lambda_handler(event, context):
    # load configs
    config = Config()

    # call gbfs for info and status endpoints

    # join info and status data

    # write to dynamo

    # write to S3

    return {
        "statusCode": 200
    }