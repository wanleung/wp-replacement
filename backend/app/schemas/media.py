from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class MediaOut(BaseModel):
    ID: int
    post_title: str
    post_mime_type: str
    guid: str
    post_date: datetime
    post_author: int
    file_url: str
    thumbnail_url: Optional[str] = None
    alt_text: str = ""
    caption: str = ""
    file_size: Optional[int] = None

    model_config = {"from_attributes": True}


class MediaListOut(BaseModel):
    items: List[MediaOut]
    total: int
    page: int
    per_page: int


class MediaUpdate(BaseModel):
    post_title: Optional[str] = None
    alt_text: Optional[str] = None
    caption: Optional[str] = None
