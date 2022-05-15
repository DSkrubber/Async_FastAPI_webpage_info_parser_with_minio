import asyncio
import pathlib
from typing import List, Set

from aiobotocore import client
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import (
    Body,
    Depends,
    FastAPI,
    HTTPException,
    Path,
    Response,
    status,
)
from pydantic import HttpUrl
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from .constants import (
    KAFKA_PARSER_TOPIC,
    KAFKA_UPDATER_TOPIC,
    WEBSITE_ROUTES,
    WEBSITE_TAG,
)
from .crud import create_db_websites, delete_db_website, get_db_website
from .db import get_db
from .errors import (
    NoSuchBucket,
    botocore_error_handler,
    dbapi_exception_handler,
    minio_client_error_handler,
    no_such_bucket_error_handler,
    sqlalchemy_exception_handler,
)
from .kafka_client import (
    consumers,
    create_producer,
    producers,
    send_kafka_message,
    update_website_parameters,
)
from .logger import get_logger
from .minio_utils import (
    clear_minio_prefix,
    generate_prefix,
    get_minio_client,
    get_presigned_urls,
)
from .schemas import (
    BadRequestErrorSchema,
    ConnectionErrorSchema,
    NotFoundErrorSchema,
    WebsiteOutSchema,
)


def get_version() -> str:
    default = "0.1.0"
    ver = pathlib.Path(__file__).parent.parent / "version.txt"
    if ver.exists() and ver.is_file():
        with open(ver, "r", encoding="utf-8") as version_info:
            line = version_info.readline().strip()
            return line or default

    return default


app = FastAPI(
    title="Async get websites info and pictures",
    version=get_version(),
)

app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(DBAPIError, dbapi_exception_handler)
app.add_exception_handler(NoSuchBucket, no_such_bucket_error_handler)
app.add_exception_handler(BotoCoreError, botocore_error_handler)
app.add_exception_handler(ClientError, minio_client_error_handler)

main_logger = get_logger(__name__)


@app.on_event("startup")
async def startup_event() -> None:
    """Creates aiokafka producer and consumer task on web application startup.

    :return: None.
    """
    await create_producer()
    asyncio.create_task(update_website_parameters())


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Stops aiokafka consumer and producer on web application shutdown.

    :return: None
    """
    producer = producers[KAFKA_PARSER_TOPIC]
    if producer:
        await producer.stop()
    consumer = consumers[KAFKA_UPDATER_TOPIC]
    if consumer:
        await consumer.stop()


@app.post(
    WEBSITE_ROUTES,
    status_code=status.HTTP_201_CREATED,
    response_model=List[WebsiteOutSchema],
    responses={
        400: {"model": BadRequestErrorSchema},
        500: {"model": ConnectionErrorSchema},
    },
    tags=[WEBSITE_TAG],
    summary="Save new website entities in database and start parsing.",
)
async def post_website(
    urls: Set[HttpUrl] = Body(
        ..., min_items=1, example={"http://site_1.com", "http://site_2.com"}
    ),
    session: AsyncSession = Depends(get_db),
) -> List[WebsiteOutSchema]:
    """Each website entity is saved in "pending" status by default. Sends kafka
    topic message for "parser" microservice to start gathering info for
    provided websites. Each website url must be unique.
    """
    websites_db = await create_db_websites(session, urls)
    website_ids = [website.website_id for website in websites_db]
    main_logger.info(f"Websites with {website_ids} ids were created")
    parser_producer = producers[KAFKA_PARSER_TOPIC] or await create_producer()
    kafka_message = {"urls": list(urls)}
    if parser_producer:
        await send_kafka_message(parser_producer, kafka_message)
    websites = [WebsiteOutSchema.from_orm(website) for website in websites_db]
    return websites


@app.get(
    WEBSITE_ROUTES + "/{website_id}",
    status_code=status.HTTP_200_OK,
    response_model=WebsiteOutSchema,
    responses={
        404: {"model": NotFoundErrorSchema},
        500: {"model": ConnectionErrorSchema},
    },
    tags=[WEBSITE_TAG],
    summary="Get parsing info and status for website_id from database.",
)
async def get_website(
    website_id: int = Path(..., example=1),
    session: AsyncSession = Depends(get_db),
) -> WebsiteOutSchema:
    """If parsing hasn't started yet - return status "pending", otherwise -
    return status "in_progress". If parsing is finished with errors - return
    status "failed". If all data ("html_length" and "pictures_keys") is parsed
    successfully - returns "finished" status.
    """
    website_db = await get_db_website(session, website_id)
    if not website_db:
        error_message = f"Website with id={website_id} was not found."
        main_logger.error(error_message)
        raise HTTPException(status_code=404, detail=error_message)
    return WebsiteOutSchema.from_orm(website_db)


@app.delete(
    WEBSITE_ROUTES + "/{website_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": NotFoundErrorSchema},
        500: {"model": ConnectionErrorSchema},
    },
    tags=[WEBSITE_TAG],
    summary="Delete website with provided website_id from database.",
)
async def delete_website(
    website_id: int = Path(..., example=1),
    session: AsyncSession = Depends(get_db),
    minio_client: client = Depends(get_minio_client),
) -> Response:
    """Also deletes all associated with website objects from minio storage."""
    website_db = await get_db_website(session, website_id)
    if not website_db:
        error_message = f"Website with id={website_id} was not found."
        main_logger.error(error_message)
        raise HTTPException(status_code=404, detail=error_message)
    await delete_db_website(session, website_db)
    keys_prefix = generate_prefix(website_db.url)
    await clear_minio_prefix(minio_client, keys_prefix)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get(
    WEBSITE_ROUTES + "/{website_id}/picture_links",
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "model": List[str],
            "content": {
                "application/json": {"example": ["url_1.jpg", "url_2.png"]},
            },
        },
        404: {"model": NotFoundErrorSchema},
        500: {"model": ConnectionErrorSchema},
    },
    tags=[WEBSITE_TAG],
    summary="Get pictures urls for website (website_id) from minio storage.",
)
async def get_pictures_links(
    website_id: int = Path(..., example=1),
    session: AsyncSession = Depends(get_db),
    minio_client: client = Depends(get_minio_client),
) -> List[str]:
    """Return array of presigned urls that will be valid for 5 minutes."""
    website_db = await get_db_website(session, website_id)
    if not website_db:
        error_message = f"Website with id={website_id} was not found."
        main_logger.error(error_message)
        raise HTTPException(status_code=404, detail=error_message)
    urls = await get_presigned_urls(minio_client, website_db.pictures_keys)
    return urls
