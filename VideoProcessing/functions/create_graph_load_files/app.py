from datetime import datetime
from random import randint
from uuid import uuid4
import boto3
import hashlib
import shortuuid

import os
import itertools
import csv
import json
from datetime import datetime

graph_load_staging_bucket = os.environ["GRAPH_LOAD_STAGING_BUCKET"]
graph_load_processing_bucket = os.environ["GRAPH_LOAD_PROCESSING_BUCKET"]
graph_load_queue = os.environ["GRAPH_LOAD_QUEUE"]
aws_region = os.environ["AWS_REGION"]
aws_account_id = os.environ["AWS_ACCOUNT_ID"]

s3 = boto3.client("s3", region_name=aws_region)

sqs_endpoint_url = f"https://sqs.{aws_region}.amazonaws.com/"
sqs = boto3.client("sqs", endpoint_url=sqs_endpoint_url)

queue_url = f"https://sqs.{aws_region}.amazonaws.com/{aws_account_id}/{graph_load_queue}"

class GraphLoadFiles:
    def __init__(self, source_name):
        self.source_name = source_name
        self.nodes = []
        self.node_ids = []
        self.edges = []
        self.edge_ids = []
        self.nodes_by_timestamp = {}  # key will be timestamp, value will be list of Labels

    def create_node(self, node, node_type="OBJECT"):
        node_id = self.get_node_id(node)
        if node_id in self.node_ids:
            print(f"Skipping existing node with id {node_id}")
        else:
            print(f"Creating node: {node['Name']}")
            node["id"] = node_id

            parent_names = [ parent["Name"] for parent in node["Parents"] ]

            node_dict = {
                ":ID": node_id,
                ":LABEL": node["Name"],
                "CONFIDENCE:Float": node["Confidence"],
                "PARENTS:String":  ", ".join(parent_names),
                "TYPE": node_type
            }
            self.nodes.append(node_dict)
            self.node_ids.append(node_id)

    def create_edge(self, node1, node2, edge_type, content_tag):
        edge_id = self.get_edge_id(node1, node2, edge_type, shortuuid.uuid())
        # if edge_id in self.edge_ids:
        #     print(f"Skipping existing edge with id {edge_id}")
        # else:
        node1_id = self.get_node_id(node1)
        node2_id = self.get_node_id(node2)
        edge_dict = {
            ":ID": self.get_edge_id(node1, node2, edge_type),
            ":START_ID": node1_id,
            ":END_ID": node2_id,
            ":TYPE": edge_type,
            "CONTENT_TAG:String": content_tag,
        }
        self.edges.append(edge_dict)
        print(f"Created {edge_type} edge between {node1['Name']} and {node2['Name']}")
        self.edge_ids.append(edge_id)

    def get_node_id(self, node):
        node_name = node["Name"]
        m = hashlib.new('sha256',
            usedforsecurity=False)
        m.update(node_name.encode())
        node_id = m.hexdigest()
        return node_id

    def get_edge_id(self, node1, node2, edge_type, salt=""):
        estring = f"{node1['Name']}-{edge_type}-{node2['Name']}-{salt}"
        m = hashlib.new('sha256',
            usedforsecurity=False)
        m.update(estring.encode())
        edge_id = m.hexdigest()
        return edge_id

    def sort_labels_by_timestamp(self, labels):
        for label in labels:
            timestamp = label["Timestamp"]
            if not timestamp in self.nodes_by_timestamp.keys():
                self.nodes_by_timestamp[timestamp] = []
            self.nodes_by_timestamp[timestamp].append(label)
        return self.nodes_by_timestamp

    def create_nodes_and_edges(self, root_node):
        self.create_node(root_node, node_type="VIDEO")
        for timestamp in self.nodes_by_timestamp.keys():
            labels = [it["Label"] for it in self.nodes_by_timestamp[timestamp]]
            for label in labels:
                self.create_node(label)
                self.create_edge(label, root_node, "APPEARS_IN", root_node["Name"])
            for e1, e2 in itertools.combinations(labels, 2):
                self.create_edge(e1, e2, "APPEARS_WITH", root_node["Name"])

    def write_nodes(self):
        outfile_path = f"{self.source_name}-nodes.csv"
        node_columns = [":ID", ":LABEL", "CONFIDENCE:Float", "PARENTS:String" , "TYPE"]
        print(f"Node Columns: {node_columns}")
        with open(os.path.join("/", "tmp", outfile_path), "w") as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=node_columns)
            dict_writer.writeheader()
            dict_writer.writerows(self.nodes)
        return outfile_path

    def write_edges(self):
        outfile_path = f"{self.source_name}-edges.csv"
        edge_columns = [":ID", ":START_ID", ":END_ID", ":TYPE", "CONTENT_TAG:String"]
        print(f"Edge Columns: {edge_columns}")
        with open(os.path.join("/", "tmp", outfile_path), "w") as output_file:
            dict_writer = csv.DictWriter(output_file, edge_columns)
            dict_writer.writeheader()
            dict_writer.writerows(self.edges)
        return outfile_path


def lambda_handler(event, context):
    print(event)

    # Put the video name in a 'nodes'ish object
    video_node = {
        "Name": event["key"],
        "Parents": [],
        "Confidence": 100.0
    }

    # Write node and edge files from detected labels

    # video_processing_job_data = event["LabelDetectionData"]
    response = s3.get_object(
        Bucket=graph_load_processing_bucket,
        Key=event["LabelDataS3Key"]
    )
    video_processing_job_data = json.load(response['Body'])

    labels = video_processing_job_data["Labels"]

    gl = GraphLoadFiles(event["key"])
    gl.sort_labels_by_timestamp(labels)
    gl.create_nodes_and_edges(video_node)
    nodes_file = gl.write_nodes()
    edges_file = gl.write_edges()

    # upload node and edge files to s3

    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    prefix = os.path.join("graph-load", timestamp)
    for outfile in [nodes_file, edges_file]:
        s3.upload_file(
            Filename=os.path.join("/", "tmp", outfile),
            Bucket=graph_load_staging_bucket,
            Key=os.path.join(prefix, outfile)
        )

    # make sure the next step can find our output
    event["GraphDataStagingBucket"] = graph_load_staging_bucket
    event["GraphDataStagingPrefix"] = prefix
    event["NodesFileKey"] = nodes_file
    event["EdgesFileKey"] = edges_file

    # add task to the graph loader queue for final load from these files to Neptune

    print("Queueing graph load")
    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(event)
    )
    print("Graph load queued")
    return event