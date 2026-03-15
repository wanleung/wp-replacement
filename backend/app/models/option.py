from sqlalchemy import BigInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.config import settings
from app.database import Base

_p = settings.WP_TABLE_PREFIX


class WPOption(Base):
    __tablename__ = f"{_p}options"

    option_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    option_name: Mapped[str] = mapped_column(String(191), nullable=False, unique=True)
    option_value: Mapped[str] = mapped_column(Text, nullable=False, default="")
    autoload: Mapped[str] = mapped_column(String(20), nullable=False, default="yes")
