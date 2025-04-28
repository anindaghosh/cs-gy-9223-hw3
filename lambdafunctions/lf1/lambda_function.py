import os
import json
import boto3
from datetime import datetime
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

# AWS clients
s3 = boto3.client("s3")
rekognition = boto3.client("rekognition")
region = os.environ["AWS_REGION"]

# AWS auth for OpenSearch
creds = boto3.Session().get_credentials()
awsauth = AWS4Auth(
    creds.access_key, creds.secret_key, region, "es", session_token=creds.token
)

# OpenSearch client
os_client = OpenSearch(
    hosts=[{"host": os.environ["OS_HOST"], "port": 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection,
)


def lambda_handler(event, context):
    # Extract bucket and key from S3 PUT event
    record = event["Records"][0]["s3"]
    bucket = record["bucket"]["name"]
    key = record["object"]["key"]

    # Detect labels via Rekognition
    rek_resp = rekognition.detect_labels(
        Image={"S3Object": {"Bucket": bucket, "Name": key}}, MaxLabels=50
    )
    rek_labels = [lbl["Name"].lower() for lbl in rek_resp["Labels"]]

    # Retrieve custom labels from S3 metadata
    head = s3.head_object(Bucket=bucket, Key=key)
    meta = head.get("Metadata", {})
    custom = meta.get("customlabels", "")
    custom_labels = [c.strip().lower() for c in custom.split(",") if c.strip()]

    # Combine labels and build document
    labels = list(set(rek_labels + custom_labels))
    doc = {
        "objectKey": key,
        "bucket": bucket,
        "createdTimestamp": datetime.utcnow().isoformat(),
        "labels": labels,
    }

    # Index into OpenSearch, if index doesn't exist, create it
    # os_client.index(index="photos", id=key, body=doc)

    # if not os_client.indices.exists(index="photos"):
    #     os_client.indices.create(index="photos")

    os_client.index(index="photos-v2", id=key, body=doc)

    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Photo indexed", "objectKey": key}),
    }
