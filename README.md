Customers want to catalog and understand their data in new ways. Unstructured data like text and video is rich with information that can deliver valuable insight. Ingesting this data is easy using AWS services. This blog presents an event driven, stateful orchestration of tasks to process incoming video and text data. When a new object is put to the ingestion bucket in Amazon S3, the PutObject Event initiates an AWS Step Function. The AWS Step Function orchestrates a series of AWS Lambda Functions that performs feature extraction using Amazon Recognition and Amazon Comprehend and then transforms and loads this data into a graph on Amazon Neptune. 

![](architecture.png)

![](stepfunctions_graph.png)