from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class TermOut(BaseModel):
    term_id: int
    name: str
    slug: str
    taxonomy: str
    description: str = ""
    parent: int = 0
    count: int = 0
    term_taxonomy_id: int

    model_config = {"from_attributes": True}


class AuthorOut(BaseModel):
    ID: int
    display_name: str
    user_login: str

    model_config = {"from_attributes": True}


class PostBase(BaseModel):
    post_title: str
    post_content: str = ""
    post_excerpt: str = ""
    post_status: str = "draft"
    post_name: str = ""
    comment_status: str = "open"
    ping_status: str = "open"
    post_password: str = ""
    menu_order: int = 0


class PostCreate(PostBase):
    post_type: str = "post"
    category_ids: List[int] = []   # term_taxonomy_ids for category
    tag_ids: List[int] = []        # term_taxonomy_ids for post_tag
    featured_image_id: Optional[int] = None


class PostUpdate(BaseModel):
    post_title: Optional[str] = None
    post_content: Optional[str] = None
    post_excerpt: Optional[str] = None
    post_status: Optional[str] = None
    post_name: Optional[str] = None
    comment_status: Optional[str] = None
    ping_status: Optional[str] = None
    post_password: Optional[str] = None
    menu_order: Optional[int] = None
    category_ids: Optional[List[int]] = None
    tag_ids: Optional[List[int]] = None
    featured_image_id: Optional[int] = None


class PostOut(PostBase):
    ID: int
    post_type: str
    post_date: datetime
    post_modified: datetime
    post_author: int
    author: Optional[AuthorOut] = None
    categories: List[TermOut] = []
    tags: List[TermOut] = []
    featured_image_url: Optional[str] = None
    featured_image_id: Optional[int] = None
    comment_count: int = 0

    model_config = {"from_attributes": True}


class PostListOut(BaseModel):
    items: List[PostOut]
    total: int
    page: int
    per_page: int
    pages: int
