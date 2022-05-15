from sqlalchemy import Column, func
from sqlalchemy.dialects.postgresql import ARRAY, ENUM, INTEGER, VARCHAR
from sqlalchemy.types import TIMESTAMP

from .db import Base
from .schemas import ParsingStatus


class Website(Base):  # type: ignore
    __tablename__ = "websites"

    website_id = Column(INTEGER, primary_key=True)
    url = Column(VARCHAR, nullable=False, unique=True)
    html_length = Column(INTEGER, nullable=True)
    pictures_keys = Column(ARRAY(VARCHAR), nullable=False, server_default="{}")
    parsing_status = Column(
        ENUM(ParsingStatus), nullable=False, default=ParsingStatus.pending
    )
    created_at = Column(
        TIMESTAMP, server_default=func.now(), nullable=False, index=True
    )

    __mapper_args__ = {"eager_defaults": True}  # to get rows without "expire".
