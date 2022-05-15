from typing import Dict, List, Optional, Set, Union

from pydantic import HttpUrl
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from .db import SessionLocal
from .logger import get_logger
from .models import Website

database_logger = get_logger(__name__)


async def create_db_websites(
    session: AsyncSession, urls: Set[HttpUrl]
) -> List[Website]:
    """Creates website entities in db table for each of provided url.

    :param session: SQLAlchemy AsyncSession connected to database.
    :param urls: websites URL of each website.
    :return: List with new created database row entities.
    """
    websites_db = [Website(url=url) for url in urls]
    session.add_all(websites_db)
    await session.commit()
    return websites_db


async def get_db_website(
    session: AsyncSession, website_id: int
) -> Optional[Website]:
    """Get website entity with provided website_id in db table.

    :param session: SQLAlchemy AsyncSession connected to database.
    :param website_id: PK value to search for.
    :return: database row entity with website_id if exists, otherwise - None.
    """
    website_db: Website = await session.get(Website, website_id)
    return website_db


async def delete_db_website(session: AsyncSession, website: Website) -> None:
    """Delete website entity with provided website_id from db table.

    :param session: SQLAlchemy AsyncSession connected to database.
    :param website: website entity to delete from database table.
    :return: None.
    """
    await session.delete(website)


async def update_db_website(
    website_url: str, update_params: Dict[str, Union[str, int]]
) -> Website:
    """Update website entity that has provided website_url in db table with

    dict of update_params parameters.
    :param website_url: unique URL value to search for.
    :param update_params: Dict with key: value pairs for Website model fields.
    :return: updated entity from database table.
    """
    async with SessionLocal() as session:
        stmt = (
            update(Website)
            .where(Website.url == website_url)
            .values(**update_params)
        )
        website_db: Website = await session.execute(stmt)
        await session.commit()
        return website_db
