import math
import mimetypes
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user, require_editor
from app.models.post import WPPost, WPPostMeta
from app.models.user import WPUser
from app.schemas.media import MediaOut, MediaListOut, MediaUpdate

router = APIRouter(prefix="/media", tags=["media"])

ALLOWED_MIME_PREFIXES = ("image/", "video/", "audio/", "application/pdf")
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


def _validate_mime(content_type: str) -> None:
    if not any(content_type.startswith(p) for p in ALLOWED_MIME_PREFIXES):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type '{content_type}' is not allowed.",
        )


def _get_upload_subdir() -> Path:
    now = datetime.now(timezone.utc)
    subdir = Path(settings.UPLOAD_DIR) / str(now.year) / f"{now.month:02d}"
    subdir.mkdir(parents=True, exist_ok=True)
    return subdir


def _media_to_out(post: WPPost, db: Session) -> MediaOut:
    alt_meta = db.query(WPPostMeta).filter(
        WPPostMeta.post_id == post.ID, WPPostMeta.meta_key == "_wp_attachment_image_alt"
    ).first()
    caption_meta = db.query(WPPostMeta).filter(
        WPPostMeta.post_id == post.ID, WPPostMeta.meta_key == "_wp_attachment_caption"
    ).first()
    size_meta = db.query(WPPostMeta).filter(
        WPPostMeta.post_id == post.ID, WPPostMeta.meta_key == "_wp_file_size"
    ).first()

    # Derive a serveable URL from the guid
    file_url = post.guid
    thumbnail_url = None
    if post.post_mime_type.startswith("image/"):
        # Try to find thumbnail (-150x150 variant)
        p = Path(settings.UPLOAD_DIR) / Path(
            post.guid.replace(f"{settings.SITE_URL}/wp-content/uploads/", "")
        )
        stem = p.stem
        suffix = p.suffix
        thumb_path = p.parent / f"{stem}-150x150{suffix}"
        if thumb_path.exists():
            thumbnail_url = post.guid.replace(
                f"{stem}{suffix}", f"{stem}-150x150{suffix}"
            )

    return MediaOut(
        ID=post.ID,
        post_title=post.post_title,
        post_mime_type=post.post_mime_type,
        guid=post.guid,
        post_date=post.post_date,
        post_author=post.post_author,
        file_url=file_url,
        thumbnail_url=thumbnail_url,
        alt_text=alt_meta.meta_value if alt_meta else "",
        caption=caption_meta.meta_value if caption_meta else "",
        file_size=int(size_meta.meta_value) if size_meta and size_meta.meta_value else None,
    )


@router.get("", response_model=MediaListOut)
def list_media(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    mime_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: WPUser = Depends(get_current_user),
):
    q = db.query(WPPost).filter(WPPost.post_type == "attachment")
    if mime_type:
        q = q.filter(WPPost.post_mime_type.ilike(f"{mime_type}%"))
    total = q.count()
    items = q.order_by(WPPost.post_date.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return MediaListOut(
        items=[_media_to_out(p, db) for p in items],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{media_id}", response_model=MediaOut)
def get_media(
    media_id: int,
    db: Session = Depends(get_db),
    current_user: WPUser = Depends(get_current_user),
):
    post = db.query(WPPost).filter(
        WPPost.ID == media_id, WPPost.post_type == "attachment"
    ).first()
    if not post:
        raise HTTPException(status_code=404, detail="Media not found")
    return _media_to_out(post, db)


@router.post("", response_model=MediaOut, status_code=status.HTTP_201_CREATED)
async def upload_media(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: WPUser = Depends(require_editor),
):
    content_type = file.content_type or mimetypes.guess_type(file.filename or "")[0] or ""
    _validate_mime(content_type)

    # Read with size limit
    chunks = []
    total = 0
    while True:
        chunk = await file.read(1024 * 1024)  # 1 MB chunks
        if not chunk:
            break
        total += len(chunk)
        if total > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File exceeds 50 MB limit",
            )
        chunks.append(chunk)
    file_bytes = b"".join(chunks)

    # Sanitize filename
    original_name = Path(file.filename or "upload").name
    safe_name = re.sub(r"[^\w.\-]", "_", original_name) if original_name else "upload"
    ext = Path(safe_name).suffix.lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"

    subdir = _get_upload_subdir()
    file_path = subdir / unique_name

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(file_bytes)

    # Generate thumbnail for images
    if content_type.startswith("image/"):
        try:
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(file_bytes))
            img.thumbnail((150, 150))
            thumb_name = f"{Path(unique_name).stem}-150x150{ext}"
            img.save(subdir / thumb_name)
        except Exception:
            pass

    # Build relative URL path (mimics WP uploads structure)
    rel = file_path.relative_to(Path(settings.UPLOAD_DIR).parent)
    file_url = f"{settings.SITE_URL}/uploads/{subdir.name}/{unique_name}"
    # Use consistent URL relative to uploads root
    year = subdir.parent.name
    month = subdir.name
    file_url = f"{settings.SITE_URL}/wp-content/uploads/{year}/{month}/{unique_name}"

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    post = WPPost(
        post_author=current_user.ID,
        post_date=now,
        post_date_gmt=now,
        post_modified=now,
        post_modified_gmt=now,
        post_title=Path(safe_name).stem,
        post_status="inherit",
        post_name=unique_name,
        post_type="attachment",
        post_mime_type=content_type,
        guid=file_url,
    )
    db.add(post)
    db.flush()

    db.add(WPPostMeta(
        post_id=post.ID,
        meta_key="_wp_attached_file",
        meta_value=f"{year}/{month}/{unique_name}",
    ))
    db.add(WPPostMeta(
        post_id=post.ID,
        meta_key="_wp_file_size",
        meta_value=str(total),
    ))
    db.commit()
    db.refresh(post)
    return _media_to_out(post, db)


@router.put("/{media_id}", response_model=MediaOut)
def update_media(
    media_id: int,
    data: MediaUpdate,
    db: Session = Depends(get_db),
    current_user: WPUser = Depends(require_editor),
):
    post = db.query(WPPost).filter(
        WPPost.ID == media_id, WPPost.post_type == "attachment"
    ).first()
    if not post:
        raise HTTPException(status_code=404, detail="Media not found")

    if data.post_title is not None:
        post.post_title = data.post_title
    if data.alt_text is not None:
        _upsert_meta(db, post.ID, "_wp_attachment_image_alt", data.alt_text)
    if data.caption is not None:
        _upsert_meta(db, post.ID, "_wp_attachment_caption", data.caption)

    db.commit()
    db.refresh(post)
    return _media_to_out(post, db)


@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_media(
    media_id: int,
    db: Session = Depends(get_db),
    current_user: WPUser = Depends(require_editor),
):
    post = db.query(WPPost).filter(
        WPPost.ID == media_id, WPPost.post_type == "attachment"
    ).first()
    if not post:
        raise HTTPException(status_code=404, detail="Media not found")

    # Try to delete the physical file
    attached = db.query(WPPostMeta).filter(
        WPPostMeta.post_id == media_id, WPPostMeta.meta_key == "_wp_attached_file"
    ).first()
    if attached and attached.meta_value:
        file_path = Path(settings.UPLOAD_DIR) / attached.meta_value
        if file_path.exists():
            file_path.unlink(missing_ok=True)
        # Also try thumbnail
        stem = file_path.stem
        suffix = file_path.suffix
        thumb = file_path.parent / f"{stem}-150x150{suffix}"
        thumb.unlink(missing_ok=True)

    db.delete(post)
    db.commit()


def _upsert_meta(db: Session, post_id: int, key: str, value: str) -> None:
    m = db.query(WPPostMeta).filter(
        WPPostMeta.post_id == post_id, WPPostMeta.meta_key == key
    ).first()
    if m:
        m.meta_value = value
    else:
        db.add(WPPostMeta(post_id=post_id, meta_key=key, meta_value=value))
