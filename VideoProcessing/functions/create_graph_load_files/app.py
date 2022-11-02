from datetime import datetime
from random import randint
from uuid import uuid4
import boto3
import hashlib

import os
import itertools
import csv

graph_load_staging_bucket = os.environ["GRAPH_LOAD_STAGING_BUCKET"]

s3 = boto3.client("s3")


class GraphLoadFiles:
    def __init__(self, source_name):
        self.source_name = source_name
        self.nodes = []
        self.edges = []
        self.nodes_by_timestamp = {}  # key will be timestamp, value will be list of Labels

    def create_node(self, node):
        print(f"Creating node: {node['Name']}")
        node["id"] = self.get_node_id(node)

        node_dict = {
            ":ID": self.get_node_id(node),
            ":Label": node["Name"],
            "confidence:Float": node["Confidence"]
        }
        self.nodes.append(node_dict)

    def create_edge(self, node1, node2, edge_type):
        node1_id = self.get_node_id(node1)
        node2_id = self.get_node_id(node2)
        edge_dict = {
            ":ID": self.get_edge_id(node1, node2, edge_type),
            ":START_ID": node1_id,
            ":END_ID": node2_id,
            ":TYPE": edge_type
        }
        self.edges.append(edge_dict)
        print(f"Created {edge_type} edge between {node1['Name']} and {node2['Name']}")

    def get_node_id(self, node):
        node_name = node["Name"]
        m = hashlib.new('md5')
        m.update(node_name.encode())
        node_id = m.hexdigest()
        return node_id

    def get_edge_id(self, node1, node2, edge_type):
        estring = f"{node1['Name']}-{edge_type}-{node2['Name']}"
        m = hashlib.new('md5')
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
        for timestamp in self.nodes_by_timestamp.keys():
            labels = [it["Label"] for it in self.nodes_by_timestamp[timestamp]]
            for label in labels:
                self.create_node(label)
                self.create_edge(label, video_node, "APPEARS_IN")
            for e1, e2 in itertools.combinations(labels, 2):
                self.create_edge(e1, e2, "APPEARS_WITH")

    def write_nodes(self):
        outfile_path = f"{self.source_name}-nodes.csv"
        node_columns = [":ID", ":Label", "confidence:Float"]
        print(f"Node Columns: {node_columns}")
        with open(os.path.join("/tmp", outfile_path), "w") as output_file:
            dict_writer = csv.DictWriter(output_file, node_columns)
            dict_writer.writeheader()
            dict_writer.writerows(self.nodes)
        return outfile_path

    def write_edges(self):
        outfile_path = f"{self.source_name}-edges.csv"
        edge_columns = [":ID", ":START_ID", ":END_ID", ":TYPE"]
        print(f"Edge Columns: {edge_columns}")
        with open(os.path.join("/tmp", outfile_path), "w") as output_file:
            dict_writer = csv.DictWriter(output_file, edge_columns)
            dict_writer.writeheader()
            dict_writer.writerows(self.edges)
        return outfile_path


def lambda_handler(event, context):
    """processes detected labels and writes node and edge files for entities and relationships


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

    # Put the video name in a 'nodes'ish object
    video_node = {
        "Type": "Video",
        "Name": event["key"]
    }

    # Wrtie node and edge files from detected labels
    gl = GraphLoadFiles(event["key"])
    gl.create_nodes_and_edges(video_node)
    nodes_file = gl.write_nodes()
    edges_file = gl.write_edges()

    # upload node and edge files to s3
    for outfile in [nodes_file, edges_file]:
        s3.upload_file(
            Filename=os.path.join("/tmp", outfile),
            Bucket=graph_load_staging_bucket,
            Key=outfile,
        )

    # make sure the next step can find our output
    event["GraphDataStagingBucket"] = graph_load_staging_bucket
    event["NodesFileKey"] = nodes_file
    event["EdgesFileKey"] = edges_file

    return event