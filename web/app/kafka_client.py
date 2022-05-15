import json
from datetime import datetime
from typing import Dict, List

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.errors import KafkaError
from pydantic import HttpUrl

from .constants import (
    KAFKA_PARSER_TOPIC,
    KAFKA_SERVER,
    KAFKA_UPDATER_TOPIC,
    UPDATER_GROUP_ID,
)
from .crud import update_db_website
from .logger import get_logger

kafka_logger = get_logger(__name__)

producers, consumers = {}, {}


async def create_producer() -> AIOKafkaProducer:
    """Creates new AIOKafkaProducer instance connected to kafka server.

    Will produce exactly one copy of message in kafka "parser" topic.
    :return: AIOKafkaProducer instance connected to bootstrap_server.
    """
    try:
        producer = AIOKafkaProducer(
            bootstrap_servers=KAFKA_SERVER,
            enable_idempotence=True,
            value_serializer=lambda msg: json.dumps(msg).encode("utf-8"),
        )
        producers[KAFKA_PARSER_TOPIC] = producer
        await producer.start()
        kafka_logger.info(f"Created producer for topic {KAFKA_PARSER_TOPIC}")
        return producer
    except KafkaError as error:
        kafka_logger.error(f"Error: Kafka producer creation error: ({error})")


async def send_kafka_message(
    producer: AIOKafkaProducer, message: Dict[str, List[HttpUrl]]
) -> None:
    """Sends provided message to "parser" topic via AIOKafkaProducer.

    :param producer: AIOKafkaProducer instance connected to bootstrap_server.
    :param message: Dict with key: values data to send via kafka topic.
    :return: None.
    """
    try:
        response = await producer.send_and_wait(KAFKA_PARSER_TOPIC, message)
        send_time = datetime.fromtimestamp(response.timestamp / 1000)
        kafka_logger.info(
            f"Message was sent to topic '{response.topic}' at {send_time} UTC"
        )
    except KafkaError as error:
        kafka_logger.error(f"Error: Kafka send message error: ({error})")


async def update_website_parameters() -> None:
    """Coroutine to run consumer in asyncio event loop.

    Recieves messages from parser microservice with website parameters
    (incl. url), deserialize message as dict and updates parameters of website
    with website_url in database.
    :return: None
    """
    try:
        consumer = AIOKafkaConsumer(
            KAFKA_UPDATER_TOPIC,
            bootstrap_servers=KAFKA_SERVER,
            group_id=UPDATER_GROUP_ID,
            auto_offset_reset="earliest",
            value_deserializer=lambda message: json.loads(message),
        )
        consumers[KAFKA_UPDATER_TOPIC] = consumer
        await consumer.start()
        await consume_messages(consumer)
    except KafkaError as error:
        kafka_logger.error(f"Kafka consumer error: ({error})")


async def consume_messages(consumer: AIOKafkaConsumer) -> None:
    """Consumes messages from kafka topic and updates website in database.

    :param consumer: AIOKafkaProducer instance connected to bootstrap_server.
    :return:
    """
    async for msg in consumer:
        kafka_logger.info(
            f"Consumed message from {msg.topic=} at {msg.timestamp=} UTC"
        )
        url = msg.value.pop("url")
        await update_db_website(url, msg.value)
