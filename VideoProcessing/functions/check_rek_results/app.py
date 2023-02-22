import os
import boto3
import json

graph_load_processing_bucket = os.environ["GRAPH_LOAD_PROCESSING_BUCKET"]

rek = boto3.client("rekognition")
s3 = boto3.client("s3")
def lambda_handler(event, context):
    print(event)

    job_id = event["job_id"]
    response = rek.get_label_detection(JobId=job_id)
    response_data = json.dumps(response)

    key = f"video_labels/{job_id}.json"
    print(f"writing rek response to {key}")
    s3.put_object(
        Bucket=graph_load_processing_bucket,
        Key=key,
        Body=response_data,
    )
    print(f"done writing rek response to s3")

    event["LabelDetectionComplete"] = response["JobStatus"]
    event["LabelDataS3Key"] = key
    # event["LabelDetectionData"] = response
    return event