import json
from datetime import datetime
from typing import Any, Dict

import phpserialize
from sqlalchemy import BigInteger, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import settings
from app.database import Base

_p = settings.WP_TABLE_PREFIX


class WPUser(Base):
    __tablename__ = f"{_p}users"

    ID: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_login: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)
    user_pass: Mapped[str] = mapped_column(String(255), nullable=False)
    user_nicename: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    user_email: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    user_url: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    user_registered: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    user_activation_key: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    user_status: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    display_name: Mapped[str] = mapped_column(String(250), nullable=False, default="")

    meta: Mapped[list["WPUserMeta"]] = relationship(
        "WPUserMeta",
        back_populates="user",
        lazy="select",
        primaryjoin="WPUser.ID == WPUserMeta.user_id",
        foreign_keys="[WPUserMeta.user_id]",
    )
    posts: Mapped[list["WPPost"]] = relationship(  # noqa: F821 (forward ref)
        "WPPost",
        back_populates="author",
        lazy="select",
        primaryjoin="WPUser.ID == WPPost.post_author",
        foreign_keys="[WPPost.post_author]",
    )

    @property
    def capabilities(self) -> Dict[str, Any]:
        """Parse wp_usermeta capabilities for role checking."""
        cap_key = f"{settings.WP_TABLE_PREFIX}capabilities"
        for m in self.meta:
            if m.meta_key == cap_key:
                val = m.meta_value or ""
                # Try PHP serialized format first (WordPress default)
                try:
                    data = phpserialize.loads(val.encode(), decode_strings=True)
                    if isinstance(data, dict):
                        return data
                except Exception:
                    pass
                # Fallback: try JSON
                try:
                    return json.loads(val) or {}
                except (json.JSONDecodeError, TypeError):
                    pass
        return {}


class WPUserMeta(Base):
    __tablename__ = f"{_p}usermeta"

    umeta_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    meta_key: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    meta_value: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped[WPUser] = relationship(
        "WPUser",
        back_populates="meta",
        primaryjoin="WPUserMeta.user_id == WPUser.ID",
        foreign_keys="[WPUserMeta.user_id]",
    )
