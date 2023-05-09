import os
import requests
import json

neptune_loader_endpoint = os.environ["NEPTUNE_LOADER_ENDPOINT"]
neptune_loader_role = os.environ["NEPTUNE_LOAD_ROLE_ARN"]
aws_region = os.environ["AWS_REGION"]

graph_load_staging_bucket = os.environ["GRAPH_LOAD_STAGING_BUCKET"]

def lambda_handler(event, context):
    print(event)

    edge_load_job_ids = []
    node_load_job_ids = []

    for record in event["Records"]:

        load_request_event = json.loads(record["body"])

        # Load the nodes
        nodes_payload = {
            "source": f"s3://{load_request_event['GraphDataStagingBucket']}/{load_request_event['GraphDataStagingPrefix']}/{load_request_event['NodesFileKey']}",
            "format": "opencypher",
            "iamRoleArn": neptune_loader_role,
            "region": aws_region,
            "failOnError": "FALSE",
            "parallelism": "MEDIUM",
            "updateSingleCardinalityProperties": "TRUE",
            "queueRequest": "TRUE",
        }

        response = requests.post(neptune_loader_endpoint, nodes_payload, timeout=10)
        print(response.text)

        result = json.loads(response.content)

        if not result["status"] == "200 OK":
            raise(Exception(f"Failed to load nodes"))

        nodes_load_id = result["payload"]["loadId"]
        node_load_job_ids.append(nodes_load_id)

        # load the edges
        edges_payload = {
            "source": f"s3://{load_request_event['GraphDataStagingBucket']}/{load_request_event['GraphDataStagingPrefix']}/{load_request_event['EdgesFileKey']}",
            "format": "opencypher",
            "iamRoleArn": neptune_loader_role,
            "region": aws_region,
            "failOnError": "FALSE",
            "parallelism": "MEDIUM",
            "updateSingleCardinalityProperties": "TRUE",
            "queueRequest": "TRUE",
            "dependencies": f"[\"{nodes_load_id}\"]"
        }

        response = requests.post(neptune_loader_endpoint, edges_payload, timeout=10)
        print(response.text)

        result = json.loads(response.content)

        if not result["status"] == "200 OK":
            raise(Exception(f"Failed to load edges"))

        edges_load_id = result["payload"]["loadId"]
        edge_load_job_ids.append(edges_load_id) #


    event["EdgeLoadJobIds"] = edge_load_job_ids
    event["NodeLoadJobIds"] = node_load_job_ids

    return event