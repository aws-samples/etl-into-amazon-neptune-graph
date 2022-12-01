import os
import requests
import json

neptune_loader_endpoint = os.environ["NEPTUNE_LOADER_ENDPOINT"]
neptune_loader_role = os.environ["NEPTUNE_LOAD_ROLE_ARN"]
aws_region = os.environ["AWS_REGION"]

graph_load_staging_bucket = os.environ["GRAPH_LOAD_PROCESSING_BUCKET"]

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

    # Load the nodes
    nodes_payload = {
        "source": f"s3://{event['GraphDataStagingBucket']}/{event['NodesFileKey']}",
        "format": "opencypher",
        "iamRoleArn": neptune_loader_role,
        "region": aws_region,
        "failOnError": "FALSE",
        "parallelism": "MEDIUM",
        "updateSingleCardinalityProperties": "FALSE",
        "queueRequest": "TRUE"
    }

    response = requests.post(neptune_loader_endpoint, nodes_payload)
    print(response.text)

    result = json.loads(response.content)

    if not result["status"] == "200 OK":
        raise(Exception(f"Failed to load nodes"))

    nodes_load_id = result["payload"]["loadId"]
    event["NodesLoadId"] = nodes_load_id

    # load the edges
    edges_payload = {
        "source": f"s3://{event['GraphDataStagingBucket']}/{event['EdgesFileKey']}",
        "format": "opencypher",
        "iamRoleArn": neptune_loader_role,
        "region": aws_region,
        "failOnError": "FALSE",
        "parallelism": "MEDIUM",
        "updateSingleCardinalityProperties": "FALSE",
        "queueRequest": "TRUE",
        "dependencies": f"[\"{nodes_load_id}\"]"
    }

    response = requests.post(neptune_loader_endpoint, edges_payload)
    print(response.text)

    result = json.loads(response.content)

    if not result["status"] == "200 OK":
        raise(Exception(f"Failed to load edges"))

    edges_load_id = result["payload"]["loadId"]
    event["EdgesLoadId"] = edges_load_id

    return event