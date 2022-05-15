from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator, Dict, List

import aiohttp
from aiobotocore.client import AioBaseClient
from aiobotocore.session import AioSession, get_session
from botocore.exceptions import BotoCoreError, ClientError

from .constants import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    MINIO_BUCKET,
    S3_ENDPOINT_URL,
)
from .logger import get_logger

minio_logger = get_logger(__name__)


@asynccontextmanager
async def get_client(session: AioSession) -> AsyncIterator[AioBaseClient]:
    """Connects to minio storage bucket with provided credentials.

    Checks that bucket exists and yields aiobotocore Session client instance
    for parser functions.
    :return: aiobotocore Session client.
    """
    async with session.create_client(
        "s3",
        endpoint_url=S3_ENDPOINT_URL,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
    ) as client:
        try:
            await client.head_bucket(Bucket=MINIO_BUCKET)
            yield client
        except ClientError as error:
            if "404" in error.args[0]:
                minio_logger.error(f"Bucket {MINIO_BUCKET} doesn't exist")
            else:
                minio_logger.error(f"Minio connection error: {error}")


async def upload_pictures_to_minio(
    webpage_url: str,
    pictures_urls: List[str],
    headers: Dict[str, str],
    aiohttp_session: aiohttp.ClientSession,
) -> List[str]:
    """Loads images data for webpage URL via aiohttp and saves data to minio.

    :param webpage_url: URL of webpage to download images for.
    :param pictures_urls: URLs of pictures to download.
    :param headers: custom user-agent header for aiohttp request.
    :param aiohttp_session: opened aiohttp session.
    :return: list of minio picture objects keys.
    """
    pictures_keys = []
    for picture_url in pictures_urls:
        key = str(
            build_key(webpage_url).with_suffix("") / build_key(picture_url)
        )
        async with aiohttp_session.get(picture_url, headers=headers) as resp:
            minio_logger.info(
                f"Response status code for {picture_url} - {resp.status}"
            )
            data = await resp.content.read()
        botocore_session = get_session()
        async with get_client(botocore_session) as minio_client:
            await save_minio_picture(minio_client, key, data)
            pictures_keys.append(key)
    minio_logger.info(f"Saved pictures for URL = {webpage_url}")
    return pictures_keys


async def save_minio_picture(
    minio_client: AioBaseClient, key: str, data: bytes
) -> None:
    """Saves bytes image data to minio storage with async client and object key

    :param minio_client: aiobotocore Session client connected to minio storage.
    :param key: new minio object's key.
    :param data: encoded picture data in bytes.
    :return: None.
    """
    try:
        await minio_client.put_object(Bucket=MINIO_BUCKET, Key=key, Body=data)
    except (ClientError, BotoCoreError) as error:
        minio_logger.error(f"Minio put_object error: {error}")


def build_key(url: str) -> Path:
    """Helper function to construct minio key parts for provided URL.

    :param url: URL to transform into key part.
    :return: pathlib Path object for key part.
    """
    return Path(url.split("://")[1].replace("/", "_"))
