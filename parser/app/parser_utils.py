import asyncio
import json
from datetime import datetime
from enum import Enum
from functools import partial
from itertools import cycle
from typing import Any, Dict, Iterator, List

from aiohttp import ClientError as ClientError
from aiohttp import ClientSession as Session
from aiohttp import ClientTimeout
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.errors import KafkaError
from bs4 import BeautifulSoup, SoupStrainer

from .constants import (
    KAFKA_PARSER_TOPIC,
    KAFKA_SERVER,
    KAFKA_UPDATER_TOPIC,
    PARSER_GROUP_ID,
    USER_AGENTS,
)
from .logger import get_logger
from .minio_utils import upload_pictures_to_minio

parser_logger = get_logger(__name__)


class ParsingStatus(str, Enum):
    in_progress = "in_progress"
    failed = "failed"
    finished = "finished"


def user_agent_cycle() -> Iterator[str]:
    """Helper function which returns an Iterator that yields user-agents in

    infinite cycle.
    :return: functools cycle for user-agents strings.
    """
    return cycle(USER_AGENTS)


async def get_producer() -> AIOKafkaProducer:
    """Connects to kafka topic, starts and returns producer with custom value

    serializer. Will produce exactly one copy of message in kafka "updater"
    topic.
    :return: AIOKafkaProducer instance.
    """
    try:
        producer = AIOKafkaProducer(
            bootstrap_servers=KAFKA_SERVER,
            enable_idempotence=True,
            value_serializer=lambda msg: json.dumps(msg).encode("utf-8"),
        )
        await producer.start()
        return producer
    except KafkaError as error:
        parser_logger.error(f"Error: Kafka producer creation error: ({error})")


async def get_consumer() -> AIOKafkaConsumer:
    """Connects to kafka "parser" topic, starts and returns consumer with

    custom value deserializer.
    :return: AIOKafkaConsumer instance.
    """
    try:
        consumer = AIOKafkaConsumer(
            KAFKA_PARSER_TOPIC,
            bootstrap_servers=KAFKA_SERVER,
            group_id=PARSER_GROUP_ID,
            auto_offset_reset="earliest",
            value_deserializer=lambda message: json.loads(message),
        )
        await consumer.start()
        return consumer
    except KafkaError as error:
        parser_logger.error(f"Error: Kafka consumer creation error: ({error})")


async def send_message(
    producer: AIOKafkaProducer, message: Dict[str, Any]
) -> None:
    """Sends provided message to "updater" topic via AIOKafkaProducer.

    :param producer: AIOKafkaProducer instance connected to bootstrap_server.
    :param message: Dict with key: values data to send via kafka topic.
    :return: None.
    """
    try:
        response = await producer.send_and_wait(KAFKA_UPDATER_TOPIC, message)
        send_time = datetime.fromtimestamp(response.timestamp / 1000)
        parser_logger.info(
            f"Message was sent to topic '{response.topic}' at {send_time} UTC"
        )
    except KafkaError as error:
        parser_logger.error(f"Error: Kafka send message error: ({error})")


def parse_data(html_page: str) -> List[str]:
    """Get list of all img href tags from provided HTML page via bs4.

    :param html_page: webpage HTML text data.
    :return: list with pictures links.
    """
    picture_links = []
    soup = BeautifulSoup(html_page, "lxml", parse_only=SoupStrainer("img"))
    for img in soup.find_all("img"):
        src = img.get("src")
        if src and src.startswith(("http://", "https://")):
            picture_links.append(src)
    return picture_links


async def load_pictures(
    url: str, producer: AIOKafkaProducer, user_agent: str
) -> None:
    """Loads html text data for webpage URL, get html length, parses images

    links for provided URL and uploads images data to minio storage
    asynchronously. Updates webpage entity data in web microservice database
    via AIOKafkaProducer. Sends "in_progress" status for pages that are going
    to be proceed, "finished" - if all data for webpage was proceeded (also
    sends html length and list of minio keys), in case of any parser errors -
    sends "failed" status.

    :param url: webpage URL to get data from.
    :param producer: AIOKafkaProducer instance connected to kafka topic.
    :param user_agent: custom user-agent to aiohttp request headers.
    :return: None.
    """
    timeout = ClientTimeout(total=60)
    headers = {"user-agent": user_agent}
    message_default: Dict[str, Any] = {
        "url": url,
        "parsing_status": ParsingStatus.in_progress,
    }
    await send_message(producer, message_default)
    async with Session(timeout=timeout, raise_for_status=True) as session:
        try:
            html = await load_page_data(session, url, headers)
            picture_parser = partial(parse_data, html_page=html)
            loop = asyncio.get_running_loop()
            # Run blocking bs4 parsing task concurrently in Executor.
            pictures_urls = await loop.run_in_executor(None, picture_parser)
            pictures_keys = await upload_pictures_to_minio(
                url, pictures_urls, headers, session
            )
            message_default.update(
                parsing_status=ParsingStatus.finished,
                html_length=len(html),
                pictures_keys=pictures_keys,
            )
            await send_message(producer, message_default)
            parser_logger.error(f"Success getting keys for {url} pictures")
        except ClientError as error:
            parser_logger.error(f"URL connection error: {error}")
            message_default.update(parsing_status=ParsingStatus.failed)
            await send_message(producer, message_default)


async def load_page_data(
    session: Session, url: str, header: Dict[str, str]
) -> str:
    """Loads webpage HTML text data via aiohttp with provided user-agent header

    :param session: opened aiohttp session.
    :param url: URLs of webpage to download.
    :param header: custom user-agent header for aiohttp request.
    :return: opened aiohttp session.
    """
    async with session.get(url, headers=header, allow_redirects=False) as page:
        parser_logger.info(f"Response status code for {url} - {page.status}")
        html: str = await page.text()
        return html
