"""
Pydantic models defining the shared award data structure.
All portal parsers must produce these models for the database layer.
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class DocumentModel(BaseModel):
    """Document metadata model."""

    doc_id: str = Field(..., description="Document identifier")
    edition: Optional[str] = Field(None, description="Document edition")
    version: Optional[str] = Field(None, description="Document version")
    reception_id: Optional[str] = Field(None, description="Reception identifier")
    official_journal_ref: Optional[str] = Field(
        None, description="Official Journal reference"
    )
    publication_date: Optional[date] = Field(None, description="Publication date")
    dispatch_date: Optional[date] = Field(None, description="Dispatch date")
    source_country: Optional[str] = Field(None, description="Source country code")
    contact_point: Optional[str] = Field(None, description="Contact point")
    phone: Optional[str] = Field(None, description="Phone number")
    email: Optional[str] = Field(None, description="Email address")
    url_general: Optional[str] = Field(None, description="General URL")
    url_buyer: Optional[str] = Field(None, description="Buyer profile URL")


class AuthorityTypeEntry(BaseModel):
    """Authority type entry."""

    code: str = Field(..., description="Authority type code")
    description: Optional[str] = Field(None, description="Authority type description")


class IdentifierEntry(BaseModel):
    """Organization identifier (e.g. SIRET, VAT, KVK)."""

    scheme: Optional[str] = Field(
        None, description="Identifier scheme (e.g. 'FR-SIRET', 'NIF')"
    )
    identifier: str = Field(..., description="Identifier value")


class ContractingBodyModel(BaseModel):
    """Contracting body model."""

    official_name: str = Field(..., description="Official name of contracting body")
    address: Optional[str] = Field(None, description="Address")
    town: Optional[str] = Field(None, description="Town/city")
    postal_code: Optional[str] = Field(None, description="Postal code")
    country_code: Optional[str] = Field(None, description="Country code")
    nuts_code: Optional[str] = Field(None, description="NUTS region code")
    authority_type: Optional[AuthorityTypeEntry] = Field(
        None, description="Authority type"
    )
    main_activity_code: Optional[str] = Field(None, description="Main activity code")
    identifiers: List[IdentifierEntry] = Field(
        default_factory=list, description="Organization identifiers"
    )


class CpvCodeEntry(BaseModel):
    """CPV code entry."""

    code: str = Field(..., description="CPV code")
    description: Optional[str] = Field(None, description="CPV code description")


class ProcedureTypeEntry(BaseModel):
    """Procedure type entry."""

    code: str = Field(..., description="Procedure type code")
    description: Optional[str] = Field(None, description="Procedure type description")


class ContractModel(BaseModel):
    """Contract model."""

    title: str = Field(..., description="Contract title")
    short_description: Optional[str] = Field(None, description="Short description")
    main_cpv_code: Optional[str] = Field(None, description="Main CPV code")
    cpv_codes: List[CpvCodeEntry] = Field(
        default_factory=list, description="All CPV codes (main + additional)"
    )
    nuts_code: Optional[str] = Field(
        None, description="NUTS code for performance location"
    )
    contract_nature_code: Optional[str] = Field(
        None, description="Contract nature code"
    )
    procedure_type: Optional[ProcedureTypeEntry] = Field(
        None, description="Procedure type"
    )
    accelerated: bool = Field(
        False, description="Accelerated procedure (eForms BT-106)"
    )
    estimated_value: Optional[Decimal] = Field(
        None, description="Pre-award estimated value (BT-27)"
    )
    estimated_value_currency: Optional[str] = Field(
        None, description="Currency of estimated value"
    )
    framework_agreement: bool = Field(False, description="Framework agreement (BT-765)")
    eu_funded: bool = Field(False, description="EU funded (BT-60)")


class ContractorModel(BaseModel):
    """Contractor model."""

    official_name: str = Field(..., description="Official name of contractor")
    address: Optional[str] = Field(None, description="Address")
    town: Optional[str] = Field(None, description="Town/city")
    postal_code: Optional[str] = Field(None, description="Postal code")
    country_code: Optional[str] = Field(None, description="Country code")
    nuts_code: Optional[str] = Field(None, description="NUTS region code")
    identifiers: List[IdentifierEntry] = Field(
        default_factory=list, description="Organization identifiers"
    )


class AwardModel(BaseModel):
    """Award model."""

    award_title: Optional[str] = Field(None, description="Award title")
    contract_number: Optional[str] = Field(None, description="Contract number")
    tenders_received: Optional[int] = Field(
        None, description="Number of tenders received"
    )
    awarded_value: Optional[float] = Field(None, description="Awarded value")
    awarded_value_currency: Optional[str] = Field(
        None, description="Awarded value currency"
    )
    award_date: Optional[date] = Field(None, description="Date of award decision")
    lot_number: Optional[str] = Field(None, description="Lot identifier")
    contract_start_date: Optional[date] = Field(
        None, description="Performance period start"
    )
    contract_end_date: Optional[date] = Field(
        None, description="Performance period end"
    )
    contractors: List[ContractorModel] = Field(
        default_factory=list, description="List of contractors"
    )


class AwardDataModel(BaseModel):
    """Complete award data model - this is what all parsers should return."""

    document: DocumentModel = Field(..., description="Document metadata")
    contracting_body: ContractingBodyModel = Field(
        ..., description="Contracting body information"
    )
    contract: ContractModel = Field(..., description="Contract information")
    awards: List[AwardModel] = Field(..., description="List of awards")

    @field_validator("awards", mode="before")
    @classmethod
    def ensure_awards_list(cls, v):
        """Ensure awards is always a list with at least one award."""
        if not v:
            raise ValueError("Awards list cannot be empty")
        return v
