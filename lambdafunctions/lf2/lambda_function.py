import json
import uuid
import boto3
import os
from opensearchpy import OpenSearch, RequestsHttpConnection  # Or elasticsearch library
from requests_aws4auth import AWS4Auth


REGION = os.environ.get("AWS_REGION")
OPENSEARCH_HOST = os.environ.get(
    "OPENSEARCH_HOST"
)  # e.g., 'search-mydomain-xyz.us-east-1.es.amazonaws.com'
OPENSEARCH_INDEX = "photos-v2"  # The index name used by LF1
LEX_BOT_ID = os.environ.get("LEX_BOT_ID")
LEX_BOT_ALIAS_ID = os.environ.get("LEX_BOT_ALIAS_ID")

credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    REGION,
    "es",
    session_token=credentials.token,
)

# Initialize OpenSearch client
os_client = OpenSearch(
    hosts=[{"host": OPENSEARCH_HOST, "port": 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection,
)

lex_client = None
if LEX_BOT_ID and LEX_BOT_ALIAS_ID:
    lex_client = boto3.client("lexv2-runtime")


def get_keywords_from_lex(query_text):
    """Uses Lex to get keywords from the query (Optional)."""
    if not lex_client:
        # If Lex isn't configured, use the raw query as keywords
        return query_text.lower().split()

    try:
        response = lex_client.recognize_text(
            botId=LEX_BOT_ID,
            botAliasId=LEX_BOT_ALIAS_ID,
            localeId="en_US",
            sessionId=str(uuid.uuid4()),
            text=query_text,
        )

        keywords = []
        if "sessionState" in response and "intent" in response["sessionState"]:
            intent_slots = response["sessionState"]["intent"].get("slots", {})
            for slot_name, slot_details in intent_slots.items():
                if (
                    slot_details
                    and "value" in slot_details
                    and slot_details["value"].get("interpretedValue")
                ):
                    keywords.append(slot_details["value"]["interpretedValue"].lower())

        if not keywords:  # Fallback if Lex doesn't find slots
            print(
                f"Lex did not return specific keywords for '{query_text}'. Using raw query instead."
            )
            return query_text.lower().split()

        print(f"Keywords from Lex: {keywords}")
        return keywords

    except Exception as e:
        print(f"Error calling Lex: {e}. Falling back to raw query.")
        return query_text.lower().split()


def search_opensearch(keywords):
    """Searches OpenSearch for photos matching the keywords."""
    if not keywords:
        return []

    search_body = {
        "query": {
            "bool": {"should": [{"match": {"labels": keyword}} for keyword in keywords]}
        },
        "_source": ["objectKey", "bucket", "labels"],
    }

    try:
        response = os_client.search(index=OPENSEARCH_INDEX, body=search_body)

        results = []
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            # Construct S3 URL (adjust region if needed)
            s3_url = f"https://{source['bucket']}.s3.{REGION}.amazonaws.com/{source['objectKey']}"
            results.append(
                {
                    "url": s3_url,
                    "labels": source.get("labels", []),  # Include labels in response
                }
            )
        return results
    except Exception as e:
        print(f"Error searching OpenSearch: {e}")
        return []


def lambda_handler(event, context):
    print(f"Received event: {json.dumps(event)}")

    query = None
    if (
        "queryStringParameters" in event
        and event["queryStringParameters"]
        and "q" in event["queryStringParameters"]
    ):
        query = event["queryStringParameters"]["q"]

    if not query:
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },  # Add CORS header
            "body": json.dumps({"message": 'Missing query parameter "q"'}),
        }

    print(f"Search query: {query}")

    keywords = get_keywords_from_lex(query)  # Use Lex or just split the query
    print(f"Using keywords: {keywords}")

    search_results = search_opensearch(keywords)
    print(f"Found {len(search_results)} results.")

    response_body = {"results": search_results}

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(response_body),
    }
