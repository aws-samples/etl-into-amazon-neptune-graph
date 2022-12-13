import os
import requests
import json

neptune_loader_endpoint = os.environ["NEPTUNE_LOADER_ENDPOINT"]
neptune_loader_role = os.environ["NEPTUNE_LOAD_ROLE_ARN"]
aws_region = os.environ["AWS_REGION"]

def lambda_handler(event, context):
    """loads data to neptune from s3


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

    edge_load_job_ids = event["EdgeLoadJobIds"]
    node_load_job_ids = event["NodeLoadJobIds"]

    load_jobs = edge_load_job_ids + node_load_job_ids

    event["LoadJobStatus"] = {}
    errors = {}

    for load_job_id in load_jobs:

        print(f"Checking load status for job with id: {load_job_id}")
        response = requests.get(f"{neptune_loader_endpoint}/{load_job_id}")
        print(response.text)

        result = json.loads(response.content)
        print(result)
        # event["LoadJobStatus"][load_job_id] = result["status"]

        job_status = result["payload"]["overallStatus"]["status"]

        if "errors" in result["payload"].keys():
            event["LoadErrors"][load_job_id] = result["payload"]["errors"]

        event["LoadJobStatus"][load_job_id] = job_status

    not_started = [ job_id for job_id in event["LoadJobStatus"] if event["LoadJobStatus"][job_id] in ["LOAD_NOT_STARTED", "LOAD_IN_QUEUE"] ]
    failed = [ job_id for job_id in event["LoadJobStatus"] if event["LoadJobStatus"][job_id] in ["LOAD_UNEXPECTED_ERROR", "LOAD_FAILED", "LOAD_S3_READ_ERROR", "LOAD_S3_ACCESS_DENIED_ERROR", "LOAD_DATA_FAILED_DUE_TO_FEED_MODIFIED_OR_DELETED", "LOAD_FAILED_BECAUSE_DEPENDENCY_NOT_SATISFIED", "LOAD_FAILED_INVALID_REQUEST"] ]
    cancelled = [ job_id for job_id in event["LoadJobStatus"] if event["LoadJobStatus"][job_id] in ["LOAD_CANCELLED_BY_USER", "LOAD_CANCELLED_DUE_TO_ERRORS", "LOAD_DATA_DEADLOCK"] ]
    completed = [ job_id for job_id in event["LoadJobStatus"] if event["LoadJobStatus"][job_id] in ["LOAD_COMPLETED"] ]
    completed_with_errors = [ job_id for job_id in event["LoadJobStatus"] if event["LoadJobStatus"][job_id] in ["LOAD_COMMITTED_W_WRITE_CONFLICTS"] ]
    running = [ job_id for job_id in event["LoadJobStatus"] if event["LoadJobStatus"][job_id] in ["LOAD_NOT_STARTED", "LOAD_IN_QUEUE"] ]

    load_failed = False
    if len(running) > 0:
        overall_status = "LOAD_IN_PROGRESS"
    elif len(failed) > 0:
        overall_status = "LOAD_FAILED"
        load_failed = True
    elif len(cancelled) > 0:
        overall_status = "LOAD_CANCELLED"
        load_failed = True
    elif len(completed) == len(edge_load_job_ids) + len(node_load_job_ids):
        overall_status = "COMPLETE"
    elif len(completed_with_errors) > 0:
        overall_status = "LOAD_COMPLETED_WITH_ERRORS"
        load_failed = True
    elif len(not_started) == len(edge_load_job_ids) + len(node_load_job_ids):
        overall_status = "LOAD_NOT_STARTED"
    else:
        raise "Invalid Job Status"

    event["LoadJobsCompleted"] = completed
    event["LoadJobsFailed"] = failed
    event["LoadJobsCancelled"] = cancelled
    event["LoadJobsRunning"] = running
    event["LoadJobsNotStarted"] = not_started
    event["LoadJobsCompletedWithErrors"] = completed_with_errors

    if load_failed:
        event["LoadStatus"] = "FAILED"
    elif overall_status == "COMPLETE":
        event["LoadStatus"] = "COMPLETE"
    else:
        event["LoadStatus"] = "NOT_COMPLETE"

    return event