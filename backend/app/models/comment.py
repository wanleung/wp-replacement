from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import settings
from app.database import Base

_p = settings.WP_TABLE_PREFIX


class WPComment(Base):
    __tablename__ = f"{_p}comments"

    comment_ID: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    comment_post_ID: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, index=True)
    comment_author: Mapped[str] = mapped_column(Text, nullable=False, default="")
    comment_author_email: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    comment_author_url: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    comment_author_IP: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    comment_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    comment_date_gmt: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    comment_content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    comment_karma: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    comment_approved: Mapped[str] = mapped_column(String(20), nullable=False, default="1")
    comment_agent: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    comment_type: Mapped[str] = mapped_column(String(20), nullable=False, default="comment")
    comment_parent: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)

    meta: Mapped[list["WPCommentMeta"]] = relationship(
        "WPCommentMeta",
        back_populates="comment",
        lazy="select",
        cascade="all, delete-orphan",
        primaryjoin="WPComment.comment_ID == WPCommentMeta.comment_id",
        foreign_keys="[WPCommentMeta.comment_id]",
    )


class WPCommentMeta(Base):
    __tablename__ = f"{_p}commentmeta"

    meta_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    comment_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    meta_key: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    meta_value: Mapped[str | None] = mapped_column(Text, nullable=True)

    comment: Mapped[WPComment] = relationship(
        "WPComment",
        back_populates="meta",
        primaryjoin="WPCommentMeta.comment_id == WPComment.comment_ID",
        foreign_keys="[WPCommentMeta.comment_id]",
    )
