from random import randint
import boto3
import os

rek = boto3.client("rekognition")


def lambda_handler(event, context):
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
        ClientRequestToken=key.strip(".mp4")
    )

    print(response)
    job_id = response["JobId"]
    event["job_id"] = job_id

    return event
