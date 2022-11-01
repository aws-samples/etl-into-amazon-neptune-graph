import json
import boto3
from aws_lambda_powertools import Metrics, Logger, Tracer
import os

print('Loading function')
step_function_arn = os.environ["VIDEO_PROCESSING_STEP_FUNCTION_ARN"]

logger = Logger()
tracer = Tracer()
metrics = Metrics()

s3 = boto3.client('s3')
rek = boto3.client('rekognition')

@metrics.log_metrics(capture_cold_start_metric=True)
@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
def lambda_handler(event, context):
    logger.info("Received event: %s", event)

    # task_failed = False

    print(f"Preparing to trigger: {step_function_arn}")

    for record in event["Records"]:
        payload = json.loads(record['body'])
        logger.info(f"Payload: %s", payload)
        for payload_record in payload["Records"]:
            logger.info(f"Payload Record: %s", payload_record)
            # try:
            bucket = payload_record["s3"]["bucket"]["name"]
            key = payload_record["s3"]["object"]["key"]
            logger.info("Bucket: %s", bucket)
            logger.info("Key: %s", key)
            # response = rek.start_label_detection(
            #     Video={
            #         'S3Object': {
            #             'Bucket': bucket,
            #             'Name': key
            #         }
            #     },
            #     NotificationChannel={
            #         'SNSTopicArn': task_complete_topic,
            #         'RoleArn': sns_role
            #     },
            #     ClientRequestToken=key.strip(".mp4")
            # )
            # logger.info("Rekognition Label Detection job submitted for %s", key)
            # logger.info("Response: %s", response)
            # except:
            #     task_failed = True
            #     logger.info("Failed to submit video object detection job")
    # return not task_failed