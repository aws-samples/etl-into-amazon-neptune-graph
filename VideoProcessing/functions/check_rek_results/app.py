from datetime import datetime
from random import randint
from uuid import uuid4
import boto3

rek = boto3.client("rekognition")
def lambda_handler(event, context):
    """Recevies label detection data for rekognition job_id from the event


    Parameters
    ----------
    event: dict, required
        Input event to the Lambda function

    context: object, required
        Lambda Context runtime methods and attributes

    Returns
    ------
        dict: Object containing details of the video processing job
    """

    print(event)

    job_id = event["job_id"]
    response = rek.get_label_detection(JobId=job_id)
    event["LabelDetectionComplete"] = response["JobStatus"]
    event["LabelDetectionData"] = response
    return event