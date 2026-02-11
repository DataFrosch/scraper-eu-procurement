"""
SQLAlchemy models for TED awards database.
Contractors and contracting bodies are normalized into shared lookup tables
with exact-match deduplication via composite unique constraints.
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional

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
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
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


class ContractingBody(Base):
    """Shared contracting body lookup table (exact-match deduplication)."""

    __tablename__ = "contracting_bodies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    official_name: Mapped[str] = mapped_column(Text, nullable=False)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    town: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    country_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    url_general: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url_buyer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    contact_point: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    authority_type_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
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
            "contact_point",
            "phone",
            "email",
            "url_general",
            "url_buyer",
            "authority_type_code",
            "main_activity_code",
            name="uq_contracting_body_identity",
            postgresql_nulls_not_distinct=True,
        ),
        Index("idx_contracting_body_country", "country_code"),
    )


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
    main_cpv_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    contract_nature_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    procedure_type_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    # Relationships
    document: Mapped["TEDDocument"] = relationship(
        "TEDDocument", back_populates="contracts"
    )
    awards: Mapped[List["Award"]] = relationship(
        "Award", back_populates="contract", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_contract_document", "ted_doc_id"),
        Index("idx_contracts_cpv", "main_cpv_code"),
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
        Numeric(15, 2), nullable=True
    )
    awarded_value_currency: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    # Relationships
    contract: Mapped["Contract"] = relationship("Contract", back_populates="awards")
    contractors: Mapped[List["Contractor"]] = relationship(
        "Contractor", secondary=award_contractors, back_populates="awards"
    )

    __table_args__ = (Index("idx_award_contract", "contract_id"),)


class Contractor(Base):
    """Shared contractor lookup table (exact-match deduplication)."""

    __tablename__ = "contractors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    official_name: Mapped[str] = mapped_column(Text, nullable=False)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    town: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    country_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
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
            name="uq_contractor_identity",
            postgresql_nulls_not_distinct=True,
        ),
        Index("idx_contractors_country", "country_code"),
    )
