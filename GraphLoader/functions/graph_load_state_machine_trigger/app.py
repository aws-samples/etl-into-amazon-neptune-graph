import json
import boto3
from aws_lambda_powertools import Metrics, Logger, Tracer
import os
import shortuuid

print('Loading function')
step_function_arn = os.environ["GRAPH_LOAD_STATE_MACHINE_ARN"]

logger = Logger()
tracer = Tracer()
metrics = Metrics()

step_functions = boto3.client("stepfunctions")

@metrics.log_metrics(capture_cold_start_metric=True)
@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
def lambda_handler(event, context):
    logger.info("Received event: %s", event)

    print(f"Preparing to trigger: {step_function_arn}")

    response = step_functions.start_execution(
        stateMachineArn=step_function_arn,
        input=json.dumps(event),
        name=shortuuid.uuid() # batch of items, each item was named by its filename coming in to avoid reprocessing
    )
    print(response)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "State Machine Executions Started"
        }),
    }