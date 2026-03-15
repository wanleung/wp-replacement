import math
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import get_current_user, require_editor
from app.models.post import WPPost
from app.models.term import WPTermRelationship, WPTermTaxonomy, WPTerm
from app.models.user import WPUser
from app.schemas.post import PostCreate, PostUpdate, PostOut, PostListOut
from app.routers._post_helpers import (
    create_post, update_post, delete_post, _build_post_out
)

router = APIRouter(prefix="/pages", tags=["pages"])


def _get_page_or_404(db: Session, page_id: int) -> WPPost:
    page = (
        db.query(WPPost)
        .options(
            joinedload(WPPost.author),
            joinedload(WPPost.meta),
            joinedload(WPPost.term_relationships).joinedload(
                WPTermRelationship.term_taxonomy
            ).joinedload(WPTermTaxonomy.term),
        )
        .filter(WPPost.ID == page_id, WPPost.post_type == "page")
        .first()
    )
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return page


@router.get("", response_model=PostListOut)
def list_pages(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: WPUser = Depends(get_current_user),
):
    q = db.query(WPPost).filter(
        WPPost.post_type == "page",
        WPPost.post_status.notin_(["auto-draft", "inherit"]),
    )
    if status:
        q = q.filter(WPPost.post_status == status)
    if search:
        q = q.filter(WPPost.post_title.ilike(f"%{search}%"))

    total = q.count()
    pages_qs = (
        q.options(
            joinedload(WPPost.author),
            joinedload(WPPost.meta),
            joinedload(WPPost.term_relationships).joinedload(
                WPTermRelationship.term_taxonomy
            ).joinedload(WPTermTaxonomy.term),
        )
        .order_by(WPPost.menu_order, WPPost.post_title)
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return PostListOut(
        items=[_build_post_out(p, db) for p in pages_qs],
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0,
    )


@router.get("/{page_id}", response_model=PostOut)
def get_page(
    page_id: int,
    db: Session = Depends(get_db),
    current_user: WPUser = Depends(get_current_user),
):
    return _build_post_out(_get_page_or_404(db, page_id), db)


@router.post("", response_model=PostOut, status_code=status.HTTP_201_CREATED)
def create_new_page(
    data: PostCreate,
    db: Session = Depends(get_db),
    current_user: WPUser = Depends(require_editor),
):
    return create_post(db, data, current_user.ID, post_type="page")


@router.put("/{page_id}", response_model=PostOut)
def update_existing_page(
    page_id: int,
    data: PostUpdate,
    db: Session = Depends(get_db),
    current_user: WPUser = Depends(require_editor),
):
    p = _get_page_or_404(db, page_id)
    return update_post(db, p, data)


@router.delete("/{page_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_page(
    page_id: int,
    db: Session = Depends(get_db),
    current_user: WPUser = Depends(require_editor),
):
    p = _get_page_or_404(db, page_id)
    delete_post(db, p)
