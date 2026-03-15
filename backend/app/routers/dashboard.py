from fastapi import APIRouter, Depends
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.post import WPPost
from app.models.comment import WPComment
from app.models.term import WPTermTaxonomy
from app.models.option import WPOption
from app.models.user import WPUser

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
def get_stats(
    db: Session = Depends(get_db),
    current_user: WPUser = Depends(get_current_user),
):
    published_posts = db.query(func.count(WPPost.ID)).filter(
        WPPost.post_type == "post", WPPost.post_status == "publish"
    ).scalar()
    draft_posts = db.query(func.count(WPPost.ID)).filter(
        WPPost.post_type == "post", WPPost.post_status == "draft"
    ).scalar()
    published_pages = db.query(func.count(WPPost.ID)).filter(
        WPPost.post_type == "page", WPPost.post_status == "publish"
    ).scalar()
    total_comments = db.query(func.count(WPComment.comment_ID)).filter(
        WPComment.comment_approved == "1"
    ).scalar()
    pending_comments = db.query(func.count(WPComment.comment_ID)).filter(
        WPComment.comment_approved == "0"
    ).scalar()
    total_media = db.query(func.count(WPPost.ID)).filter(
        WPPost.post_type == "attachment"
    ).scalar()
    categories_count = db.query(func.count(WPTermTaxonomy.term_taxonomy_id)).filter(
        WPTermTaxonomy.taxonomy == "category"
    ).scalar()
    tags_count = db.query(func.count(WPTermTaxonomy.term_taxonomy_id)).filter(
        WPTermTaxonomy.taxonomy == "post_tag"
    ).scalar()

    # Recent posts
    recent_posts = (
        db.query(WPPost)
        .filter(WPPost.post_type == "post", WPPost.post_status == "publish")
        .order_by(WPPost.post_date.desc())
        .limit(5)
        .all()
    )

    return {
        "posts": {"published": published_posts, "draft": draft_posts},
        "pages": {"published": published_pages},
        "comments": {"approved": total_comments, "pending": pending_comments},
        "media": total_media,
        "categories": categories_count,
        "tags": tags_count,
        "recent_posts": [
            {
                "ID": p.ID,
                "post_title": p.post_title,
                "post_date": p.post_date.isoformat(),
                "post_status": p.post_status,
            }
            for p in recent_posts
        ],
    }
