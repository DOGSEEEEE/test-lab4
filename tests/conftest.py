import pytest
import boto3
from botocore.config import Config
from services.config import *
from services.db import get_dynamodb_resource

@pytest.fixture(scope="session", autouse=True)
def setup_localstack_resources():
    # Налаштування для DynamoDB з фейковими ключами
    dynamo_client = boto3.client(
        "dynamodb",
        endpoint_url=AWS_ENDPOINT_URL,
        region_name=AWS_REGION,
        aws_access_key_id="test",
        aws_secret_access_key="test"
    )
    
    # Перевірка та створення таблиці
    existing_tables = dynamo_client.list_tables()["TableNames"]
    if SHIPPING_TABLE_NAME not in existing_tables:
        dynamo_client.create_table(
            TableName=SHIPPING_TABLE_NAME,
            KeySchema=[{"AttributeName": "shipping_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "shipping_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        dynamo_client.get_waiter("table_exists").wait(TableName=SHIPPING_TABLE_NAME)
    
    # Налаштування для SQS з фейковими ключами та відключенням валідації параметрів
    sqs_client = boto3.client(
        "sqs",
        endpoint_url=AWS_ENDPOINT_URL, 
        region_name=AWS_REGION,
        aws_access_key_id="test",
        aws_secret_access_key="test",
        # ЦЕЙ РЯДОК ВИПРАВЛЯЄ ПОМИЛКУ 500:
        config=Config(parameter_validation=False, signature_version='s3v4')
    )
    
    # Створення черги
    response = sqs_client.create_queue(QueueName=SHIPPING_QUEUE)
    queue_url = response["QueueUrl"]

    yield  # Тут виконуються всі тести

    # Очищення після тестів
    try:
        dynamo_client.delete_table(TableName=SHIPPING_TABLE_NAME)
        sqs_client.delete_queue(QueueUrl=queue_url)
    except Exception:
        pass # Якщо ресурси вже видалені, ігноруємо помилку


@pytest.fixture
def dynamo_resource():
    return get_dynamodb_resource()