from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .constants import (
    POSTGRES_DB,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_USER,
)

SQLALCHEMY_POSTGRESQL_URL = "postgresql+asyncpg://{0}:{1}@{2}:{3}/{4}".format(
    POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB
)
engine = create_async_engine(SQLALCHEMY_POSTGRESQL_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    class_=AsyncSession,
    bind=engine,
    expire_on_commit=False,
)

Base = declarative_base()


async def get_db() -> AsyncIterator[AsyncSession]:
    """Yields async SessionLocal instance for FastAPI resources.

    Finally, closes connection to database.
    :return: Iterator that yields SessionLocal instance.
    """
    async with SessionLocal() as db:
        yield db
