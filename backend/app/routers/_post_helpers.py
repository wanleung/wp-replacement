"""
Shared helpers for post CRUD (used by both /posts and /pages routers).
"""
import re
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.models.post import WPPost, WPPostMeta
from app.models.term import WPTermTaxonomy, WPTermRelationship
from app.models.user import WPUser
from app.schemas.post import PostCreate, PostUpdate, PostOut, TermOut, AuthorOut


def _slugify(text: str) -> str:
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug)
    return slug[:200]


def _ensure_unique_slug(db: Session, slug: str, post_type: str, exclude_id: int = 0) -> str:
    base = slug or "post"
    candidate = base
    n = 1
    while True:
        q = db.query(WPPost).filter(
            WPPost.post_name == candidate,
            WPPost.post_type == post_type,
        )
        if exclude_id:
            q = q.filter(WPPost.ID != exclude_id)
        if not q.first():
            return candidate
        candidate = f"{base}-{n}"
        n += 1


def _get_term_taxs(db: Session, ids: List[int], taxonomy: str) -> List[WPTermTaxonomy]:
    return (
        db.query(WPTermTaxonomy)
        .filter(
            WPTermTaxonomy.term_taxonomy_id.in_(ids),
            WPTermTaxonomy.taxonomy == taxonomy,
        )
        .all()
    )


def _get_postmeta(db: Session, post_id: int, key: str) -> Optional[str]:
    m = (
        db.query(WPPostMeta)
        .filter(WPPostMeta.post_id == post_id, WPPostMeta.meta_key == key)
        .first()
    )
    return m.meta_value if m else None


def _set_postmeta(db: Session, post_id: int, key: str, value: str) -> None:
    m = (
        db.query(WPPostMeta)
        .filter(WPPostMeta.post_id == post_id, WPPostMeta.meta_key == key)
        .first()
    )
    if m:
        m.meta_value = value
    else:
        db.add(WPPostMeta(post_id=post_id, meta_key=key, meta_value=value))


def _build_post_out(post: WPPost, db: Session) -> PostOut:
    categories: List[TermOut] = []
    tags: List[TermOut] = []
    featured_image_url: Optional[str] = None
    featured_image_id: Optional[int] = None

    # Rebuild term lists
    for rel in post.term_relationships:
        tt = rel.term_taxonomy
        if tt is None:
            continue
        term = tt.term
        tobj = TermOut(
            term_id=term.term_id,
            name=term.name,
            slug=term.slug,
            taxonomy=tt.taxonomy,
            description=tt.description,
            parent=tt.parent,
            count=tt.count,
            term_taxonomy_id=tt.term_taxonomy_id,
        )
        if tt.taxonomy == "category":
            categories.append(tobj)
        elif tt.taxonomy == "post_tag":
            tags.append(tobj)

    # Thumbnail
    thumb_id_str = _get_postmeta(db, post.ID, "_thumbnail_id")
    if thumb_id_str:
        try:
            thumb_id = int(thumb_id_str)
            featured_image_id = thumb_id
            thumb_post = db.query(WPPost).filter(WPPost.ID == thumb_id).first()
            if thumb_post:
                featured_image_url = thumb_post.guid
        except (ValueError, TypeError):
            pass

    author_out = None
    if post.author:
        author_out = AuthorOut(
            ID=post.author.ID,
            display_name=post.author.display_name,
            user_login=post.author.user_login,
        )

    return PostOut(
        ID=post.ID,
        post_author=post.post_author,
        author=author_out,
        post_title=post.post_title,
        post_content=post.post_content,
        post_excerpt=post.post_excerpt,
        post_status=post.post_status,
        post_name=post.post_name,
        post_type=post.post_type,
        post_date=post.post_date,
        post_modified=post.post_modified,
        comment_status=post.comment_status,
        ping_status=post.ping_status,
        post_password=post.post_password,
        menu_order=post.menu_order,
        categories=categories,
        tags=tags,
        featured_image_url=featured_image_url,
        featured_image_id=featured_image_id,
        comment_count=post.comment_count,
    )


def create_post(
    db: Session,
    data: PostCreate,
    author_id: int,
    post_type: str = "post",
) -> PostOut:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    slug = _ensure_unique_slug(
        db,
        data.post_name or _slugify(data.post_title),
        post_type,
    )
    post = WPPost(
        post_author=author_id,
        post_date=now,
        post_date_gmt=now,
        post_modified=now,
        post_modified_gmt=now,
        post_content=data.post_content,
        post_title=data.post_title,
        post_excerpt=data.post_excerpt,
        post_status=data.post_status,
        post_name=slug,
        comment_status=data.comment_status,
        ping_status=data.ping_status,
        post_password=data.post_password,
        menu_order=data.menu_order,
        post_type=post_type,
        guid=f"{settings.SITE_URL}/?p=0",
    )
    db.add(post)
    db.flush()

    # Update GUID with real ID
    post.guid = f"{settings.SITE_URL}/?p={post.ID}"

    # Assign terms
    all_tt_ids = data.category_ids + data.tag_ids
    for tt_id in all_tt_ids:
        rel = WPTermRelationship(object_id=post.ID, term_taxonomy_id=tt_id)
        db.add(rel)
        tt = db.query(WPTermTaxonomy).filter(
            WPTermTaxonomy.term_taxonomy_id == tt_id
        ).first()
        if tt:
            tt.count = tt.count + 1

    # Featured image
    if data.featured_image_id is not None:
        _set_postmeta(db, post.ID, "_thumbnail_id", str(data.featured_image_id))

    db.commit()
    db.refresh(post)
    return _build_post_out(post, db)


def update_post(db: Session, post: WPPost, data: PostUpdate) -> PostOut:
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    if data.post_title is not None:
        post.post_title = data.post_title
    if data.post_content is not None:
        post.post_content = data.post_content
    if data.post_excerpt is not None:
        post.post_excerpt = data.post_excerpt
    if data.post_status is not None:
        post.post_status = data.post_status
    if data.comment_status is not None:
        post.comment_status = data.comment_status
    if data.ping_status is not None:
        post.ping_status = data.ping_status
    if data.post_password is not None:
        post.post_password = data.post_password
    if data.menu_order is not None:
        post.menu_order = data.menu_order
    if data.post_name is not None:
        post.post_name = _ensure_unique_slug(
            db, data.post_name, post.post_type, exclude_id=post.ID
        )

    post.post_modified = now
    post.post_modified_gmt = now

    # Update term relationships
    if data.category_ids is not None or data.tag_ids is not None:
        # Remove old relationships
        old_rels = (
            db.query(WPTermRelationship)
            .join(
                WPTermTaxonomy,
                WPTermRelationship.term_taxonomy_id == WPTermTaxonomy.term_taxonomy_id,
            )
            .filter(
                WPTermRelationship.object_id == post.ID,
                WPTermTaxonomy.taxonomy.in_(["category", "post_tag"]),
            )
            .all()
        )
        for rel in old_rels:
            tt = db.query(WPTermTaxonomy).filter(
                WPTermTaxonomy.term_taxonomy_id == rel.term_taxonomy_id
            ).first()
            if tt and tt.count > 0:
                tt.count = tt.count - 1
            db.delete(rel)
        db.flush()

        new_ids = (data.category_ids or []) + (data.tag_ids or [])
        for tt_id in new_ids:
            rel = WPTermRelationship(object_id=post.ID, term_taxonomy_id=tt_id)
            db.add(rel)
            tt = db.query(WPTermTaxonomy).filter(
                WPTermTaxonomy.term_taxonomy_id == tt_id
            ).first()
            if tt:
                tt.count = tt.count + 1

    # Featured image
    if data.featured_image_id is not None:
        _set_postmeta(db, post.ID, "_thumbnail_id", str(data.featured_image_id))

    db.commit()
    db.refresh(post)
    return _build_post_out(post, db)


def delete_post(db: Session, post: WPPost) -> None:
    # Decrement term counts
    for rel in post.term_relationships:
        tt = db.query(WPTermTaxonomy).filter(
            WPTermTaxonomy.term_taxonomy_id == rel.term_taxonomy_id
        ).first()
        if tt and tt.count > 0:
            tt.count = tt.count - 1
    db.delete(post)
    db.commit()
