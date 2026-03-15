from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
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

router = APIRouter(prefix="/posts", tags=["posts"])


def _get_post_or_404(db: Session, post_id: int, post_type: str = "post") -> WPPost:
    post = (
        db.query(WPPost)
        .options(
            joinedload(WPPost.author),
            joinedload(WPPost.meta),
            joinedload(WPPost.term_relationships).joinedload(
                WPTermRelationship.term_taxonomy
            ).joinedload(WPTermTaxonomy.term),
        )
        .filter(WPPost.ID == post_id, WPPost.post_type == post_type)
        .first()
    )
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.get("", response_model=PostListOut)
def list_posts(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: WPUser = Depends(get_current_user),
):
    q = db.query(WPPost).filter(
        WPPost.post_type == "post",
        WPPost.post_status.notin_(["auto-draft", "inherit"]),
    )
    if status:
        q = q.filter(WPPost.post_status == status)
    if search:
        q = q.filter(
            WPPost.post_title.ilike(f"%{search}%")
            | WPPost.post_content.ilike(f"%{search}%")
        )
    if category_id:
        q = q.join(WPPost.term_relationships).filter(
            WPPost.term_relationships.any(term_taxonomy_id=category_id)
        )

    total = q.count()
    posts = (
        q.options(
            joinedload(WPPost.author),
            joinedload(WPPost.meta),
            joinedload(WPPost.term_relationships).joinedload(
                WPTermRelationship.term_taxonomy
            ).joinedload(WPTermTaxonomy.term),
        )
        .order_by(WPPost.post_date.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    import math
    return PostListOut(
        items=[_build_post_out(p, db) for p in posts],
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0,
    )


@router.get("/{post_id}", response_model=PostOut)
def get_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: WPUser = Depends(get_current_user),
):
    return _build_post_out(_get_post_or_404(db, post_id, "post"), db)


@router.post("", response_model=PostOut, status_code=status.HTTP_201_CREATED)
def create_new_post(
    data: PostCreate,
    db: Session = Depends(get_db),
    current_user: WPUser = Depends(require_editor),
):
    data.post_type = "post"
    return create_post(db, data, current_user.ID, post_type="post")


@router.put("/{post_id}", response_model=PostOut)
def update_existing_post(
    post_id: int,
    data: PostUpdate,
    db: Session = Depends(get_db),
    current_user: WPUser = Depends(require_editor),
):
    post = _get_post_or_404(db, post_id, "post")
    return update_post(db, post, data)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: WPUser = Depends(require_editor),
):
    post = _get_post_or_404(db, post_id, "post")
    delete_post(db, post)
