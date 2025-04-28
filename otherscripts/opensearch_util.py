import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
from requests_aws4auth import AWS4Auth
import json

# Set up AWS credentials and region
region = "us-east-1"  # Your region
service = "es"

# Get credentials
credentials = boto3.Session(profile_name="default").get_credentials()

print(credentials.access_key)
print(credentials.secret_key)

awsauth = AWSV4SignerAuth(credentials, region, service)

# OpenSearch endpoint - replace with your endpoint
host = "search-hw3-photos-wb2elafbufjqz5tj5lycoy7pvu.us-east-1.es.amazonaws.com"  # Your domain endpoint

# Create OpenSearch client
opensearch_client = OpenSearch(
    hosts=[{"host": host, "port": 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection,
)

print(opensearch_client.info())


# Create index if it doesn't exist
if not opensearch_client.indices.exists(index="photos-v2"):
    # Create index with mapping
    index_body = {
        "mappings": {
            "properties": {
                "objectKey": {"type": "keyword"},
                "bucket": {"type": "keyword"},
                "createdTimestamp": {
                    "type": "date",
                    "format": "strict_date_optional_time||epoch_millis",
                },
                "labels": {"type": "text", "analyzer": "english"},
            }
        }
    }

    response = opensearch_client.indices.create(index="photos-v2", body=index_body)

    print(f"Index created: {response}")
