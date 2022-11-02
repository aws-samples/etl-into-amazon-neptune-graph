from datetime import datetime
from random import randint
from uuid import uuid4
import boto3

rek = boto3.client("rekognition")
def lambda_handler(event, context):
    """Sample Lambda function which mocks the operation of selling a random number
    of shares for a stock.

    For demonstration purposes, this Lambda function does not actually perform any 
    actual transactions. It simply returns a mocked result.

    Parameters
    ----------
    event: dict, required
        Input event to the Lambda function

    context: object, required
        Lambda Context runtime methods and attributes

    Returns
    ------
        dict: Object containing details of the stock selling transaction
    """

    print(event)

    job_id = event["job_id"]
    response = rek.get_label_detection(JobId=job_id)
    event["LabelDetectionComplete"] = response["JobStatus"]
    event["LabelDetectionData"] = response
    return event