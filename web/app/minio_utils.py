import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List

from aiobotocore.client import AioBaseClient
from aiobotocore.session import get_session
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError

from .constants import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    MINIO_BUCKET,
    MINIO_EXTERNAL_URL,
    S3_ENDPOINT_URL,
)
from .errors import NoSuchBucket
from .logger import get_logger

minio_logger = get_logger(__name__)


async def get_minio_client() -> AsyncIterator[AioBaseClient]:
    """Connects to minio storage bucket with provided credentials.

    Checks that bucket exists and yields aiobotocore Session client instance
    for FastAPI resources.
    :return: aiobotocore Session client.
    """
    session = get_session()
    async with session.create_client(
        "s3",
        endpoint_url=S3_ENDPOINT_URL,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        config=Config(signature_version="s3v4"),
    ) as minio_client:
        try:
            minio_client.head_bucket(Bucket=MINIO_BUCKET)
        except ClientError as error:
            minio_logger.warning(f"Minio connection error: {error}")
            if "404" in error.args[0]:
                raise NoSuchBucket(f"Bucket {MINIO_BUCKET} doesn't exist")
            raise
        yield minio_client


async def clear_minio_prefix(minio_client: AioBaseClient, prefix: str) -> None:
    """Clears all objects in storage with specified prefix in keys.

    :param minio_client: aiobotocore Session client connected to minio storage.
    :param prefix: objects key prefix.
    :return: None.
    """
    files = await list_minio_prefix_files(minio_client, prefix)
    for file_obj in files:
        try:
            await minio_client.delete_object(
                Bucket=MINIO_BUCKET, Key=file_obj["Key"]
            )
        except (ClientError, BotoCoreError) as error:
            minio_logger.warning(f"Minio file delete error: {error}")
            raise


FileInfo = List[Dict[str, Any]]


async def list_minio_prefix_files(
    minio_client: AioBaseClient, prefix: str
) -> FileInfo:
    """Returns "Contents" field from result of boto3 list_objects_v2 if exists.

    :param minio_client: aiobotocore Session client connected to minio storage.
    :param prefix: objects key prefix.
    :return: list of dicts with files properties if exists.
    """
    try:
        files: Dict[str, FileInfo] = await minio_client.list_objects_v2(
            Bucket=MINIO_BUCKET, Prefix=prefix
        )
        return files.get("Contents", [])
    except (ClientError, BotoCoreError) as error:
        minio_logger.warning(f"Minio list objects error: {error}")
        raise


async def get_presigned_urls(
    minio_client: AioBaseClient, picture_keys: List[str]
) -> List[str]:
    """Returns List of generated presigned_urls for provided picture_keys.

    :param minio_client: aiobotocore Session client connected to minio storage.
    :param picture_keys: keys of minio objects.
    :return: List of presigned URLs.
    """
    tasks = [
        generate_url(minio_client, picture_key) for picture_key in picture_keys
    ]
    presigned_urls = await asyncio.gather(*tasks)
    return list(presigned_urls)


async def generate_url(minio_client: AioBaseClient, picture_key: str) -> str:
    """Generates presigned_url for provided key that expires after 5 minutes.

    :param minio_client: aiobotocore Session client connected to minio storage.
    :param picture_key: key of minio objects.
    :return: generated presigned url.
    """
    async with minio_host_modifier(minio_client) as client:
        try:
            url: str = await client.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": MINIO_BUCKET, "Key": picture_key},
                ExpiresIn=300,
            )
            return url
        except (ClientError, BotoCoreError) as error:
            minio_logger.error(f"Minio generate presigned url error: {error}")
            raise


@asynccontextmanager
async def minio_host_modifier(
    client: AioBaseClient,
) -> AsyncIterator[AioBaseClient]:
    """Async context manager to modify minio host to externally accessible.

    :param client: aiobotocore Session client connected to minio storage.
    :return: Iterator that yields aiobotocore Session client.
    """
    client.meta._endpoint_url = MINIO_EXTERNAL_URL
    try:
        yield client
    finally:
        client.meta._endpoint_url = S3_ENDPOINT_URL


def generate_prefix(site_url: str) -> str:
    """Helper function to construct minio key prefix for provided URL.

    :param website_url: URL to transform.
    :return: key prefix.
    """
    prefix = Path(site_url.split("://")[1].replace("/", "_")).with_suffix("")
    return str(prefix)
