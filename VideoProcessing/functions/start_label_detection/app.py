from random import randint
import boto3
import os

rek_complete_topic = os.environ["SNS_TOPIC"]
rek_complete_topic_role = os.environ["SNS_ROLE"]

rek = boto3.client("rekognition")


def lambda_handler(event, context):
    """Sample Lambda function which mocks the operation of checking the current price 
    of a stock.

    For demonstration purposes this Lambda function simply returns 
    a random integer between 0 and 100 as the stock price.

    Parameters
    ----------
    event: dict, required
        Input event to the Lambda function

    context: object, required
        Lambda Context runtime methods and attributes

    Returns
    ------
        dict: Object containing the current price of the stock
    """
    # Check current price of the stock
    print(event)
    bucket = event["bucket"]
    key = event["key"]

    response = rek.start_label_detection(
        Video={
                "S3Object": {
                "Bucket": bucket,
                "Name": key
            }
        },
        NotificationChannel={
            'SNSTopicArn': rek_complete_topic,
            'RoleArn': rek_complete_topic_role
        },
        ClientRequestToken=key.strip(".mp4")
    )

    print(response)
    job_id = response["JobId"]
    event["job_id"] = job_id

    return event
