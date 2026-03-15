from typing import Optional, List
from pydantic import BaseModel


class TermBase(BaseModel):
    name: str
    slug: str = ""
    description: str = ""
    parent: int = 0


class CategoryCreate(TermBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    parent: Optional[int] = None


class TagCreate(TermBase):
    pass


class TagUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None


class TermOut(BaseModel):
    term_id: int
    term_taxonomy_id: int
    name: str
    slug: str
    description: str
    parent: int
    count: int
    taxonomy: str

    model_config = {"from_attributes": True}


class TermListOut(BaseModel):
    items: List[TermOut]
    total: int
