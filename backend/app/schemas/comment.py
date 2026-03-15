from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class CommentCreate(BaseModel):
    comment_post_ID: int
    comment_content: str
    comment_author: str = ""
    comment_author_email: str = ""
    comment_author_url: str = ""
    comment_parent: int = 0


class CommentUpdate(BaseModel):
    comment_content: Optional[str] = None
    comment_approved: Optional[str] = None


class CommentOut(BaseModel):
    comment_ID: int
    comment_post_ID: int
    comment_author: str
    comment_author_email: str
    comment_author_url: str
    comment_date: datetime
    comment_content: str
    comment_approved: str
    comment_parent: int
    user_id: int

    model_config = {"from_attributes": True}


class CommentListOut(BaseModel):
    items: List[CommentOut]
    total: int
    page: int
    per_page: int
