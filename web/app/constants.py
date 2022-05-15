import os

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

APP_HOST = os.environ.get("APP_HOST", "localhost")
APP_PORT = os.environ.get("APP_PORT", 8080)

POSTGRES_USER = os.environ.get("POSTGRES_USER", "admin")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "admin")
POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.environ.get("POSTGRES_PORT", 5432)
POSTGRES_DB = os.environ.get("POSTGRES_DB", "postgres")

S3_ENDPOINT_URL = os.environ.get("S3_ENDPOINT_URL", "http://localhost:9000")
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "minioadmin")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "minioadmin")
MINIO_BUCKET = os.environ.get("MINIO_BUCKET", "test")
MINIO_EXTERNAL_URL = os.environ.get(
    "MINIO_EXTERNAL_URL", "http://localhost:9000"
)

KAFKA_HOST = os.environ.get("KAFKA_HOST", "kafka")
KAFKA_PORT = os.environ.get("KAFKA_PORT", 9092)
KAFKA_SERVER = f"{KAFKA_HOST}:{KAFKA_PORT}"
KAFKA_PARSER_TOPIC = os.environ.get("KAFKA_PARSER_TOPIC", "parser")
KAFKA_UPDATER_TOPIC = os.environ.get("KAFKA_UPDATER_TOPIC", "updater")
UPDATER_GROUP_ID = "updaters"

WEBSITE_ROUTES = "/websites"
WEBSITE_TAG = "Websites info"
