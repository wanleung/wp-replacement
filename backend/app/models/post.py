from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import settings
from app.database import Base

_p = settings.WP_TABLE_PREFIX


class WPPost(Base):
    __tablename__ = f"{_p}posts"

    ID: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    post_author: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, index=True)
    post_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    post_date_gmt: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    post_content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    post_title: Mapped[str] = mapped_column(Text, nullable=False, default="")
    post_excerpt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    post_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft", index=True
    )
    comment_status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")
    ping_status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")
    post_password: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    post_name: Mapped[str] = mapped_column(String(200), nullable=False, default="", index=True)
    to_ping: Mapped[str] = mapped_column(Text, nullable=False, default="")
    pinged: Mapped[str] = mapped_column(Text, nullable=False, default="")
    post_modified: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )
    post_modified_gmt: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )
    post_content_filtered: Mapped[str] = mapped_column(Text, nullable=False, default="")
    post_parent: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, index=True)
    guid: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    menu_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    post_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="post", index=True
    )
    post_mime_type: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    comment_count: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)

    author: Mapped["WPUser"] = relationship(  # noqa: F821
        "WPUser",
        back_populates="posts",
        primaryjoin="WPPost.post_author == WPUser.ID",
        foreign_keys="[WPPost.post_author]",
        lazy="joined",
    )
    meta: Mapped[list["WPPostMeta"]] = relationship(
        "WPPostMeta",
        back_populates="post",
        lazy="select",
        cascade="all, delete-orphan",
        primaryjoin="WPPost.ID == WPPostMeta.post_id",
        foreign_keys="[WPPostMeta.post_id]",
    )
    term_relationships: Mapped[list["WPTermRelationship"]] = relationship(
        "WPTermRelationship",
        back_populates="post",
        lazy="select",
        cascade="all, delete-orphan",
        primaryjoin="WPPost.ID == WPTermRelationship.object_id",
        foreign_keys="[WPTermRelationship.object_id]",
    )


class WPPostMeta(Base):
    __tablename__ = f"{_p}postmeta"

    meta_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    meta_key: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    meta_value: Mapped[str | None] = mapped_column(Text, nullable=True)

    post: Mapped[WPPost] = relationship(
        "WPPost",
        back_populates="meta",
        primaryjoin="WPPostMeta.post_id == WPPost.ID",
        foreign_keys="[WPPostMeta.post_id]",
    )
