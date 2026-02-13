"""
SQLAlchemy models for TED awards database.
Contractors and contracting bodies are normalized into shared lookup tables
with exact-match deduplication via composite unique constraints.
"""

from datetime import date
from decimal import Decimal
from typing import ClassVar, List, Optional

from sqlalchemy import (
    Column,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Table,
    Text,
    Index,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    validates,
)


def _normalize_country_code(value: Optional[str]) -> Optional[str]:
    """Normalize country codes to uppercase (ISO standard)."""
    return value.upper() if value else value


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class UpsertMixin:
    """Mixin for models that support upsert (INSERT ... ON CONFLICT DO UPDATE).

    Subclasses declare their conflict target and update behavior, then call
    Model.upsert(session, values_dict) instead of hand-written upsert functions.
    """

    __upsert_constraint__: ClassVar[str | None] = None
    __upsert_index_elements__: ClassVar[list[str] | None] = None
    __upsert_returning__: ClassVar[str | None] = None

    @classmethod
    def _upsert_set(cls, excluded):
        """Return the set_ dict for ON CONFLICT DO UPDATE SET."""
        raise NotImplementedError

    @classmethod
    def upsert(cls, session: Session, values: dict) -> int | None:
        """Insert or update a row. Returns the returning column value, or None."""
        conflict = {}
        if cls.__upsert_constraint__:
            conflict["constraint"] = cls.__upsert_constraint__
        else:
            conflict["index_elements"] = cls.__upsert_index_elements__

        stmt = pg_insert(cls).values(**values)
        stmt = stmt.on_conflict_do_update(
            **conflict, set_=cls._upsert_set(stmt.excluded)
        )

        if cls.__upsert_returning__:
            stmt = stmt.returning(getattr(cls, cls.__upsert_returning__))
            return session.execute(stmt).scalar_one()

        session.execute(stmt)
        return None


# Junction table for many-to-many relationship between awards and contractors
award_contractors = Table(
    "award_contractors",
    Base.metadata,
    Column(
        "award_id",
        Integer,
        ForeignKey("awards.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "contractor_id",
        Integer,
        ForeignKey("contractors.id"),
        primary_key=True,
    ),
)


class CpvCode(UpsertMixin, Base):
    """CPV code lookup table with code as natural primary key."""

    __tablename__ = "cpv_codes"
    __upsert_index_elements__: ClassVar[list[str]] = ["code"]

    code: Mapped[str] = mapped_column(String, primary_key=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    @classmethod
    def _upsert_set(cls, excluded):
        return {"description": func.coalesce(excluded.description, cls.description)}


class ProcedureType(UpsertMixin, Base):
    """Procedure type lookup table with code as natural primary key."""

    __tablename__ = "procedure_types"
    __upsert_index_elements__: ClassVar[list[str]] = ["code"]

    code: Mapped[str] = mapped_column(String, primary_key=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    @classmethod
    def _upsert_set(cls, excluded):
        return {"description": func.coalesce(excluded.description, cls.description)}


class AuthorityType(UpsertMixin, Base):
    """Authority type lookup table with code as natural primary key."""

    __tablename__ = "authority_types"
    __upsert_index_elements__: ClassVar[list[str]] = ["code"]

    code: Mapped[str] = mapped_column(String, primary_key=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    @classmethod
    def _upsert_set(cls, excluded):
        return {"description": func.coalesce(excluded.description, cls.description)}


# Junction table for many-to-many relationship between contracts and CPV codes
contract_cpv_codes = Table(
    "contract_cpv_codes",
    Base.metadata,
    Column(
        "contract_id",
        Integer,
        ForeignKey("contracts.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "cpv_code",
        String,
        ForeignKey("cpv_codes.code"),
        primary_key=True,
    ),
)


class ContractingBody(UpsertMixin, Base):
    """Shared contracting body lookup table (exact-match deduplication)."""

    __tablename__ = "contracting_bodies"
    __upsert_constraint__: ClassVar[str] = "uq_contracting_body_identity"
    __upsert_returning__: ClassVar[str] = "id"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    official_name: Mapped[str] = mapped_column(Text, nullable=False)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    town: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    country_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    nuts_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    authority_type_code: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("authority_types.code"), nullable=True
    )
    main_activity_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    # Relationships
    documents: Mapped[List["TEDDocument"]] = relationship(
        "TEDDocument", back_populates="contracting_body"
    )

    __table_args__ = (
        UniqueConstraint(
            "official_name",
            "address",
            "town",
            "postal_code",
            "country_code",
            "nuts_code",
            "authority_type_code",
            "main_activity_code",
            name="uq_contracting_body_identity",
            postgresql_nulls_not_distinct=True,
        ),
        Index("idx_contracting_body_country", "country_code"),
        Index("idx_contracting_body_nuts", "nuts_code"),
    )

    @classmethod
    def _upsert_set(cls, excluded):
        return {"official_name": excluded.official_name}


class TEDDocument(Base):
    """Main TED document metadata."""

    __tablename__ = "ted_documents"

    doc_id: Mapped[str] = mapped_column(String, primary_key=True)
    edition: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    version: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    reception_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    official_journal_ref: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    publication_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    dispatch_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    source_country: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    contact_point: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    url_general: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url_buyer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    contracting_body_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("contracting_bodies.id"), nullable=False
    )
    # Relationships
    contracting_body: Mapped["ContractingBody"] = relationship(
        "ContractingBody", back_populates="documents"
    )
    contracts: Mapped[List["Contract"]] = relationship(
        "Contract", back_populates="document", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_ted_documents_pub_date", "publication_date"),
        Index("idx_ted_documents_country", "source_country"),
    )

    @validates("source_country")
    def validate_source_country(self, key, value):
        return _normalize_country_code(value)


class Contract(Base):
    """Contract objects (the main procurement items)."""

    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ted_doc_id: Mapped[str] = mapped_column(
        String, ForeignKey("ted_documents.doc_id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    short_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    main_cpv_code: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("cpv_codes.code"), nullable=True
    )
    contract_nature_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    nuts_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    procedure_type_code: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("procedure_types.code"), nullable=True
    )
    # Relationships
    document: Mapped["TEDDocument"] = relationship(
        "TEDDocument", back_populates="contracts"
    )
    awards: Mapped[List["Award"]] = relationship(
        "Award", back_populates="contract", cascade="all, delete-orphan"
    )
    cpv_codes: Mapped[List["CpvCode"]] = relationship(
        "CpvCode", secondary=contract_cpv_codes
    )

    __table_args__ = (
        Index("idx_contract_document", "ted_doc_id"),
        Index("idx_contracts_nuts", "nuts_code"),
    )


class Award(Base):
    """Contract awards (the actual winners)."""

    __tablename__ = "awards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contract_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False
    )
    contract_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    award_title: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tenders_received: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    awarded_value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(24, 2), nullable=True
    )
    awarded_value_currency: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    # Relationships
    contract: Mapped["Contract"] = relationship("Contract", back_populates="awards")
    contractors: Mapped[List["Contractor"]] = relationship(
        "Contractor", secondary=award_contractors, back_populates="awards"
    )

    __table_args__ = (Index("idx_award_contract", "contract_id"),)


class Contractor(UpsertMixin, Base):
    """Shared contractor lookup table (exact-match deduplication)."""

    __tablename__ = "contractors"
    __upsert_constraint__: ClassVar[str] = "uq_contractor_identity"
    __upsert_returning__: ClassVar[str] = "id"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    official_name: Mapped[str] = mapped_column(Text, nullable=False)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    town: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    country_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    nuts_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    # Relationships
    awards: Mapped[List["Award"]] = relationship(
        "Award", secondary=award_contractors, back_populates="contractors"
    )

    __table_args__ = (
        UniqueConstraint(
            "official_name",
            "address",
            "town",
            "postal_code",
            "country_code",
            "nuts_code",
            name="uq_contractor_identity",
            postgresql_nulls_not_distinct=True,
        ),
        Index("idx_contractors_country", "country_code"),
        Index("idx_contractors_nuts", "nuts_code"),
    )

    @classmethod
    def _upsert_set(cls, excluded):
        return {"official_name": excluded.official_name}
