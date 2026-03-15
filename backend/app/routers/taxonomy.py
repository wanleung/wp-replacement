import re
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_editor
from app.models.term import WPTerm, WPTermTaxonomy
from app.models.user import WPUser
from app.schemas.term import (
    CategoryCreate, CategoryUpdate, TagCreate, TagUpdate, TermOut, TermListOut
)

router = APIRouter(tags=["taxonomy"])


def _slugify(text: str) -> str:
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug)
    return slug[:200]


def _ensure_unique_slug(db: Session, slug: str, taxonomy: str, exclude_id: int = 0) -> str:
    base = slug or "term"
    candidate = base
    n = 1
    while True:
        q = (
            db.query(WPTerm)
            .join(WPTermTaxonomy, WPTerm.term_id == WPTermTaxonomy.term_id)
            .filter(WPTerm.slug == candidate, WPTermTaxonomy.taxonomy == taxonomy)
        )
        if exclude_id:
            q = q.filter(WPTerm.term_id != exclude_id)
        if not q.first():
            return candidate
        candidate = f"{base}-{n}"
        n += 1


def _tt_to_out(tt: WPTermTaxonomy) -> TermOut:
    return TermOut(
        term_id=tt.term.term_id,
        term_taxonomy_id=tt.term_taxonomy_id,
        name=tt.term.name,
        slug=tt.term.slug,
        description=tt.description,
        parent=tt.parent,
        count=tt.count,
        taxonomy=tt.taxonomy,
    )


# ── Categories ──────────────────────────────────────────────────────────────

categories_router = APIRouter(prefix="/categories", tags=["categories"])


@categories_router.get("", response_model=TermListOut)
def list_categories(
    db: Session = Depends(get_db),
    current_user: WPUser = Depends(get_current_user),
    search: str = Query(""),
):
    q = (
        db.query(WPTermTaxonomy)
        .join(WPTerm, WPTermTaxonomy.term_id == WPTerm.term_id)
        .filter(WPTermTaxonomy.taxonomy == "category")
    )
    if search:
        q = q.filter(WPTerm.name.ilike(f"%{search}%"))
    items = q.order_by(WPTerm.name).all()
    return TermListOut(items=[_tt_to_out(t) for t in items], total=len(items))


@categories_router.get("/{term_taxonomy_id}", response_model=TermOut)
def get_category(
    term_taxonomy_id: int,
    db: Session = Depends(get_db),
    current_user: WPUser = Depends(get_current_user),
):
    tt = (
        db.query(WPTermTaxonomy)
        .filter(
            WPTermTaxonomy.term_taxonomy_id == term_taxonomy_id,
            WPTermTaxonomy.taxonomy == "category",
        )
        .first()
    )
    if not tt:
        raise HTTPException(status_code=404, detail="Category not found")
    return _tt_to_out(tt)


@categories_router.post("", response_model=TermOut, status_code=status.HTTP_201_CREATED)
def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: WPUser = Depends(require_editor),
):
    slug = _ensure_unique_slug(db, data.slug or _slugify(data.name), "category")
    term = WPTerm(name=data.name, slug=slug)
    db.add(term)
    db.flush()
    tt = WPTermTaxonomy(
        term_id=term.term_id,
        taxonomy="category",
        description=data.description,
        parent=data.parent,
    )
    db.add(tt)
    db.commit()
    db.refresh(tt)
    return _tt_to_out(tt)


@categories_router.put("/{term_taxonomy_id}", response_model=TermOut)
def update_category(
    term_taxonomy_id: int,
    data: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: WPUser = Depends(require_editor),
):
    tt = (
        db.query(WPTermTaxonomy)
        .filter(
            WPTermTaxonomy.term_taxonomy_id == term_taxonomy_id,
            WPTermTaxonomy.taxonomy == "category",
        )
        .first()
    )
    if not tt:
        raise HTTPException(status_code=404, detail="Category not found")
    if data.name is not None:
        tt.term.name = data.name
    if data.slug is not None:
        tt.term.slug = _ensure_unique_slug(
            db, data.slug, "category", exclude_id=tt.term_id
        )
    if data.description is not None:
        tt.description = data.description
    if data.parent is not None:
        tt.parent = data.parent
    db.commit()
    db.refresh(tt)
    return _tt_to_out(tt)


@categories_router.delete("/{term_taxonomy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    term_taxonomy_id: int,
    db: Session = Depends(get_db),
    current_user: WPUser = Depends(require_editor),
):
    tt = (
        db.query(WPTermTaxonomy)
        .filter(
            WPTermTaxonomy.term_taxonomy_id == term_taxonomy_id,
            WPTermTaxonomy.taxonomy == "category",
        )
        .first()
    )
    if not tt:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(tt)
    db.delete(tt.term)
    db.commit()


# ── Tags ─────────────────────────────────────────────────────────────────────

tags_router = APIRouter(prefix="/tags", tags=["tags"])


@tags_router.get("", response_model=TermListOut)
def list_tags(
    db: Session = Depends(get_db),
    current_user: WPUser = Depends(get_current_user),
    search: str = Query(""),
):
    q = (
        db.query(WPTermTaxonomy)
        .join(WPTerm, WPTermTaxonomy.term_id == WPTerm.term_id)
        .filter(WPTermTaxonomy.taxonomy == "post_tag")
    )
    if search:
        q = q.filter(WPTerm.name.ilike(f"%{search}%"))
    items = q.order_by(WPTerm.name).all()
    return TermListOut(items=[_tt_to_out(t) for t in items], total=len(items))


@tags_router.get("/{term_taxonomy_id}", response_model=TermOut)
def get_tag(
    term_taxonomy_id: int,
    db: Session = Depends(get_db),
    current_user: WPUser = Depends(get_current_user),
):
    tt = (
        db.query(WPTermTaxonomy)
        .filter(
            WPTermTaxonomy.term_taxonomy_id == term_taxonomy_id,
            WPTermTaxonomy.taxonomy == "post_tag",
        )
        .first()
    )
    if not tt:
        raise HTTPException(status_code=404, detail="Tag not found")
    return _tt_to_out(tt)


@tags_router.post("", response_model=TermOut, status_code=status.HTTP_201_CREATED)
def create_tag(
    data: TagCreate,
    db: Session = Depends(get_db),
    current_user: WPUser = Depends(require_editor),
):
    slug = _ensure_unique_slug(db, data.slug or _slugify(data.name), "post_tag")
    term = WPTerm(name=data.name, slug=slug)
    db.add(term)
    db.flush()
    tt = WPTermTaxonomy(
        term_id=term.term_id,
        taxonomy="post_tag",
        description=data.description,
        parent=0,
    )
    db.add(tt)
    db.commit()
    db.refresh(tt)
    return _tt_to_out(tt)


@tags_router.put("/{term_taxonomy_id}", response_model=TermOut)
def update_tag(
    term_taxonomy_id: int,
    data: TagUpdate,
    db: Session = Depends(get_db),
    current_user: WPUser = Depends(require_editor),
):
    tt = (
        db.query(WPTermTaxonomy)
        .filter(
            WPTermTaxonomy.term_taxonomy_id == term_taxonomy_id,
            WPTermTaxonomy.taxonomy == "post_tag",
        )
        .first()
    )
    if not tt:
        raise HTTPException(status_code=404, detail="Tag not found")
    if data.name is not None:
        tt.term.name = data.name
    if data.slug is not None:
        tt.term.slug = _ensure_unique_slug(
            db, data.slug, "post_tag", exclude_id=tt.term_id
        )
    if data.description is not None:
        tt.description = data.description
    db.commit()
    db.refresh(tt)
    return _tt_to_out(tt)


@tags_router.delete("/{term_taxonomy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(
    term_taxonomy_id: int,
    db: Session = Depends(get_db),
    current_user: WPUser = Depends(require_editor),
):
    tt = (
        db.query(WPTermTaxonomy)
        .filter(
            WPTermTaxonomy.term_taxonomy_id == term_taxonomy_id,
            WPTermTaxonomy.taxonomy == "post_tag",
        )
        .first()
    )
    if not tt:
        raise HTTPException(status_code=404, detail="Tag not found")
    db.delete(tt)
    db.delete(tt.term)
    db.commit()
