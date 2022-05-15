from datetime import datetime
from enum import Enum
from typing import Optional, Set

from pydantic import BaseModel, Field


class ConnectionErrorSchema(BaseModel):
    detail: str

    class Config:
        schema_extra = {
            "example": {"detail": "Error: Connection error."},
        }


class NotFoundErrorSchema(BaseModel):
    detail: str

    class Config:
        schema_extra = {
            "example": {"detail": "Error: Resource was not found."},
        }


class BadRequestErrorSchema(BaseModel):
    detail: str

    class Config:
        schema_extra = {
            "example": {"detail": "Error: Bad request."},
        }


class ParsingStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    failed = "failed"
    finished = "finished"


class WebsiteOutSchema(BaseModel):

    website_id: int = Field(..., example=1)
    url: str = Field(..., example="http://site_1.com")
    html_length: Optional[int] = Field(None, example=1024)
    pictures_keys: Set[str] = Field(
        ..., example={"site/picture_1.jpeg", "site/picture_2.png"}
    )
    parsing_status: ParsingStatus = Field(
        ..., example=ParsingStatus.in_progress
    )
    created_at: datetime = Field(..., example="2021-10-19 01:01:01")

    class Config:
        orm_mode = True
