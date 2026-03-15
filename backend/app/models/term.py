from sqlalchemy import BigInteger, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import settings
from app.database import Base

_p = settings.WP_TABLE_PREFIX


class WPTerm(Base):
    __tablename__ = f"{_p}terms"

    term_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    slug: Mapped[str] = mapped_column(String(200), nullable=False, default="", index=True)
    term_group: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)

    taxonomies: Mapped[list["WPTermTaxonomy"]] = relationship(
        "WPTermTaxonomy",
        back_populates="term",
        lazy="select",
        primaryjoin="WPTerm.term_id == WPTermTaxonomy.term_id",
        foreign_keys="[WPTermTaxonomy.term_id]",
    )


class WPTermTaxonomy(Base):
    __tablename__ = f"{_p}term_taxonomy"

    term_taxonomy_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    term_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    taxonomy: Mapped[str] = mapped_column(String(32), nullable=False, default="", index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    parent: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    count: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)

    term: Mapped[WPTerm] = relationship(
        "WPTerm",
        back_populates="taxonomies",
        primaryjoin="WPTermTaxonomy.term_id == WPTerm.term_id",
        foreign_keys="[WPTermTaxonomy.term_id]",
    )
    relationships: Mapped[list["WPTermRelationship"]] = relationship(
        "WPTermRelationship",
        back_populates="term_taxonomy",
        lazy="select",
        primaryjoin="WPTermTaxonomy.term_taxonomy_id == WPTermRelationship.term_taxonomy_id",
        foreign_keys="[WPTermRelationship.term_taxonomy_id]",
    )


class WPTermRelationship(Base):
    __tablename__ = f"{_p}term_relationships"

    object_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    term_taxonomy_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    term_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    post: Mapped["WPPost"] = relationship(  # noqa: F821
        "WPPost",
        back_populates="term_relationships",
        primaryjoin="WPTermRelationship.object_id == WPPost.ID",
        foreign_keys="[WPTermRelationship.object_id]",
    )
    term_taxonomy: Mapped[WPTermTaxonomy] = relationship(
        "WPTermTaxonomy",
        back_populates="relationships",
        primaryjoin="WPTermRelationship.term_taxonomy_id == WPTermTaxonomy.term_taxonomy_id",
        foreign_keys="[WPTermRelationship.term_taxonomy_id]",
    )
