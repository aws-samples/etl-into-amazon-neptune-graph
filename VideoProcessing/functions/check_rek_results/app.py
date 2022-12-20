import os
import boto3
import json

graph_load_processing_bucket = os.environ["GRAPH_LOAD_PROCESSING_BUCKET"]

rek = boto3.client("rekognition")
s3 = boto3.client("s3")
def lambda_handler(event, context):
    """Receives label detection data for rekognition job_id from the event


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
    response_data = json.dumps(response)

    key = f"video_labels/{job_id}.json"
    s3.put_object(
        Bucket=graph_load_processing_bucket,
        Key=key,
        Body=response_data,
    )

    event["LabelDetectionComplete"] = response["JobStatus"]
    event["LabelDataS3Key"] = key
    # event["LabelDetectionData"] = response
    return event