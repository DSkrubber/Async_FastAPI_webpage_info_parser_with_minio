import os

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

APP_HOST = os.environ.get("APP_HOST", "localhost")
APP_PORT = os.environ.get("APP_PORT", 8081)

S3_ENDPOINT_URL = os.environ.get("S3_ENDPOINT_URL", "http://localhost:9000")
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "minioadmin")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "minioadmin")
MINIO_BUCKET = os.environ.get("MINIO_BUCKET", "test")

KAFKA_HOST = os.environ.get("KAFKA_HOST", "kafka")
KAFKA_PORT = os.environ.get("KAFKA_PORT", 9092)
KAFKA_PARSER_TOPIC = os.environ.get("KAFKA_PARSER_TOPIC", "parser")
KAFKA_UPDATER_TOPIC = os.environ.get("KAFKA_UPDATER_TOPIC", "updater")

PARSER_GROUP_ID = "parsers"

with open("./app/user_agents.txt") as agents_file:
    USER_AGENTS = [agent.rstrip() for agent in agents_file]
