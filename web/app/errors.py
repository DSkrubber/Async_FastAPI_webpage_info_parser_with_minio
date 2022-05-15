from botocore.exceptions import BotoCoreError, ClientError
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError, SQLAlchemyError

from .crud import database_logger


class NoSuchBucket(Exception):
    """Custom exception that will be raised if minio bucket doesn't exist."""

    def __init__(self, message: str):
        self.message = message


def sqlalchemy_exception_handler(
    request: Request, error: SQLAlchemyError
) -> JSONResponse:
    database_logger.error(error)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Error: SQLAlchemy error ({error})"},
    )


def dbapi_exception_handler(
    request: Request, error: DBAPIError
) -> JSONResponse:
    database_logger.error(error.__cause__)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Error: DBAPI error ({error.__cause__})"},
    )


def no_such_bucket_error_handler(
    request: Request, exc: NoSuchBucket
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"detail": f"Error: {exc.message}"},
    )


def botocore_error_handler(
    request: Request, exc: BotoCoreError
) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"detail": f"Error: {exc}"},
    )


def minio_client_error_handler(
    request: Request, exc: ClientError
) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"detail": f"Error: {exc}"},
    )
