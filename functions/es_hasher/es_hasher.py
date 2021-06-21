import json
import logging
import boto3
import os
import certifi
import hashlib
from aws_requests_auth.aws_auth import AWSRequestsAuth
from elasticsearch import Elasticsearch, RequestsHttpConnection
from common_lib import detailed_exception

# Log level
logging.basicConfig()
LOGGER = logging.getLogger()
if os.environ["DEBUG_MODE"] == "true":
    LOGGER.setLevel(logging.DEBUG)
else:
    LOGGER.setLevel(logging.INFO)

# Get AWS region and necessary clients
# REGION = boto3.session.Session().region_name
# EVENTS_TABLE = os.environ["EVENTS_TABLE_NAME"]
# NEWS_TABLE = os.environ["NEWS_TABLE_NAME"]
# BLOGS_TABLE = os.environ["BLOGS_TABLE_NAME"]
ES_HASH_TABLE = os.environ["ES_HASH_TABLE_NAME"]
DYNAMODB_RESOURCE = boto3.resource("dynamodb")

REGION = boto3.session.Session().region_name
ES_ENDPOINT = os.environ['ES_DOMAIN']


# Create the auth token for the sigv4 signature
SESSION = boto3.session.Session()
CREDENTIALS = SESSION.get_credentials().get_frozen_credentials()
AWS_AUTH = AWSRequestsAuth(
    aws_access_key=CREDENTIALS.access_key,
    aws_secret_access_key=CREDENTIALS.secret_key,
    aws_token=CREDENTIALS.token,
    aws_host=ES_ENDPOINT,
    aws_region=REGION,
    aws_service='es'
)

# Connect to the elasticsearch cluster using aws authentication. The lambda function
# must have access in an IAM policy to the ES cluster.
ES_CLIENT = Elasticsearch(
    hosts=[{'host': ES_ENDPOINT, 'port': 443}],
    http_auth=AWS_AUTH,
    use_ssl=True,
    verify_certs=True,
    ca_certs=certifi.where(),
    timeout=120,
    connection_class=RequestsHttpConnection
)


def lambda_handler(event, context):
    """
    Lambda entry-point
    """
    try:
        # Get all hashes of all items currently in Elasticsearch via ESHash DynamoDB Table
        hash_table = DYNAMODB_RESOURCE.Table(ES_HASH_TABLE)
        response = hash_table.scan()
        es_hash_items = response["Items"]
        while response.get("LastEvaluatedKey") in response:
            response = hash_table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
            es_hash_items.extend(response["Items"])

        es_hash_list_map = {
            "Events": [],
            "News": [],
            "Blogs": [],
            "Clubs": []
        }
        # Separate the hashes in the ESHashTable by document type into individual lists
        for es_item_hash_string in es_hash_items:
            es_hash_list_map.get(es_item_hash_string["documentType"]).append(es_item_hash_string["documentHash"])

        # Update ESHashTable and Elasticsearch with respect to events, news and blogs
        for table_name in ["Events", "News", "Blogs", "Clubs"]:
            # Get all items for the specific table_name
            item_table = DYNAMODB_RESOURCE.Table(f"{table_name}Table")
            response = item_table.scan(ConsistentRead=True)
            table_items = response["Items"]
            while response.get("LastEvaluatedKey") in response:
                response = item_table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
                table_items.extend(response["Items"])

            # Hash all items in the item table
            item_hash_list = []
            for item in table_items:
                item_hash = hashlib.md5(str(item).encode("utf-8")).hexdigest()
                item_hash_list.append(item_hash)

            for es_item_hash_string in es_hash_list_map.get(table_name):
                if es_item_hash_string not in item_hash_list:
                    # If an item hash is in the ESHashTable but not the datastore tables
                    # That item is outdated and should be removed from ESHashTable and Elasticsearch
                    hash_table.delete_item(Key={"documentHash": es_item_hash_string})
                    ES_CLIENT.delete(index=table_name.lower(), id=es_item_hash_string)

            # Insert new items from item table into hashtable and Elasticsearch
            for index, item in enumerate(table_items):
                if item_hash_list[index] not in es_hash_list_map.get(table_name):
                    # If an item hash is in the datastore table but not in the ESHashTable
                    # That item is new and should be added to ESHashTable and Elasticsearch
                    hash_table.put_item(Item={
                        "documentHash": item_hash_list[index],
                        "documentType": table_name
                    })
                    ES_CLIENT.index(index=table_name.lower(), body=item, id=item_hash_list[index])
    except Exception as e:
        detailed_exception(LOGGER)
        return {"status": "error"}

    return {"status": "completed"}
