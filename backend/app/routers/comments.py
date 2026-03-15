import math
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_editor
from app.models.comment import WPComment
from app.models.post import WPPost
from app.models.user import WPUser
from app.schemas.comment import CommentCreate, CommentUpdate, CommentOut, CommentListOut
from datetime import datetime, timezone

router = APIRouter(prefix="/comments", tags=["comments"])


def _get_comment_or_404(db: Session, comment_id: int) -> WPComment:
    c = db.query(WPComment).filter(WPComment.comment_ID == comment_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Comment not found")
    return c


@router.get("", response_model=CommentListOut)
def list_comments(
    post_id: int = Query(0),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    approved_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: WPUser = Depends(get_current_user),
):
    q = db.query(WPComment)
    if post_id:
        q = q.filter(WPComment.comment_post_ID == post_id)
    if approved_only:
        q = q.filter(WPComment.comment_approved == "1")
    total = q.count()
    items = q.order_by(WPComment.comment_date.asc()).offset((page - 1) * per_page).limit(per_page).all()
    return CommentListOut(items=items, total=total, page=page, per_page=per_page)


@router.post("", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def create_comment(
    data: CommentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: WPUser = Depends(get_current_user),
):
    post = db.query(WPPost).filter(WPPost.ID == data.comment_post_ID).first()
    if not post or post.comment_status == "closed":
        raise HTTPException(status_code=400, detail="Comments are closed for this post")

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    comment = WPComment(
        comment_post_ID=data.comment_post_ID,
        comment_author=data.comment_author or current_user.display_name,
        comment_author_email=data.comment_author_email or current_user.user_email,
        comment_author_url=data.comment_author_url,
        comment_author_IP=request.client.host if request.client else "",
        comment_date=now,
        comment_date_gmt=now,
        comment_content=data.comment_content,
        comment_approved="1",
        comment_agent=request.headers.get("user-agent", ""),
        comment_parent=data.comment_parent,
        user_id=current_user.ID,
    )
    db.add(comment)
    # Update comment count
    post.comment_count = post.comment_count + 1
    db.commit()
    db.refresh(comment)
    return comment


@router.put("/{comment_id}", response_model=CommentOut)
def update_comment(
    comment_id: int,
    data: CommentUpdate,
    db: Session = Depends(get_db),
    current_user: WPUser = Depends(require_editor),
):
    comment = _get_comment_or_404(db, comment_id)
    if data.comment_content is not None:
        comment.comment_content = data.comment_content
    if data.comment_approved is not None:
        comment.comment_approved = data.comment_approved
    db.commit()
    db.refresh(comment)
    return comment


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: WPUser = Depends(require_editor),
):
    comment = _get_comment_or_404(db, comment_id)
    post = db.query(WPPost).filter(WPPost.ID == comment.comment_post_ID).first()
    db.delete(comment)
    if post and post.comment_count > 0:
        post.comment_count = post.comment_count - 1
    db.commit()
