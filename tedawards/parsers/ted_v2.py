"""
TED Version 2.0 parser - unified parser for all TED 2.0 variants.
Handles R2.0.7, R2.0.8, and R2.0.9 formats (2008-2023).

Date formats in TED 2.0:
- DATE_PUB, DS_DATE_DISPATCH, DELETION_DATE: YYYYMMDD (e.g., "20110104")
- DATE_CONCLUSION_CONTRACT (R2.0.9): YYYY-MM-DD (e.g., "2014-01-06")
- CONTRACT_AWARD_DATE (R2.0.7/R2.0.8): nested <DAY>/<MONTH>/<YEAR> XML elements
"""

import logging
import re
from datetime import date
from pathlib import Path
from typing import List, Optional

from lxml import etree

from ..schema import (
    TedAwardDataModel,
    DocumentModel,
    ContractingBodyModel,
    ContractModel,
    CpvCodeEntry,
    ProcedureTypeEntry,
    AuthorityTypeEntry,
    AwardModel,
    ContractorModel,
)
from .monetary import parse_monetary_value
from .xml import (
    elem_text,
    elem_attr,
    element_text,
)

# Mapping from old-style authority type codes (R2.0.7/R2.0.8 CODED_DATA_SECTION)
# to canonical codes (R2.0.9 CA_TYPE VALUE). Verified empirically: R2.0.9 XML files
# contain both old and new codes, confirming these are exact 1:1 mappings.
# Code 8 ("Other") maps ~99% to CA_TYPE_OTHER free-text and ~1% to EU_INSTITUTION
# (international orgs shoehorned into "Other"). We map 8 -> OTHER since that's the
# intent for the vast majority. Code Z ("Not specified") has no R2.0.9 equivalent;
# R2.0.9 simply omits CA_TYPE, so we map it to None.
_AUTHORITY_TYPE_CODE_MAP: dict[str, str | None] = {
    "1": "MINISTRY",
    "3": "REGIONAL_AUTHORITY",
    "5": "EU_INSTITUTION",
    "6": "BODY_PUBLIC",
    "8": "OTHER",
    "N": "NATIONAL_AGENCY",
    "R": "REGIONAL_AGENCY",
    "Z": None,
}

# Human-readable descriptions for authority type codes, from TED schema documentation
_AUTHORITY_TYPE_DESCRIPTIONS: dict[str, str] = {
    "MINISTRY": "Ministry or any other national or federal authority",
    "REGIONAL_AUTHORITY": "Regional or local authority",
    "EU_INSTITUTION": "European institution/agency or international organisation",
    "BODY_PUBLIC": "Body governed by public law",
    "OTHER": "Other type",
    "NATIONAL_AGENCY": "National or federal agency/office",
    "REGIONAL_AGENCY": "Regional or local agency/office",
}

# Mapping from old-style contract nature codes (R2.0.7/R2.0.8 NC_CONTRACT_NATURE CODE)
# to canonical codes (R2.0.9 TYPE_CONTRACT CTYPE). Verified empirically from F03_2014
# dual-code files containing both NC_CONTRACT_NATURE and TYPE_CONTRACT:
# "1" -> WORKS (1,961 matches), "2" -> SUPPLIES (5,049), "4" -> SERVICES (6,226).
_CONTRACT_NATURE_CODE_MAP: dict[str, str] = {
    "1": "WORKS",
    "2": "SUPPLIES",
    "4": "SERVICES",
}


def _normalize_contract_nature_code(raw_code: Optional[str]) -> Optional[str]:
    """Normalize a contract nature code to canonical R2.0.9 uppercase form.

    Old-style numeric codes are mapped; eForms lowercase codes are uppercased.
    Already-canonical codes pass through unchanged.
    """
    if raw_code is None:
        return None

    if raw_code in _CONTRACT_NATURE_CODE_MAP:
        return _CONTRACT_NATURE_CODE_MAP[raw_code]

    return raw_code.upper()


# Mapping from old-style procedure type codes (R2.0.7/R2.0.8 PR_PROC CODE) to canonical
# codes (R2.0.9 PT_* element names). Verified empirically from F03_2014 dual-code files.
# Note: code "4" maps to different PT_* values depending on form type; for award notices
# (Form 3 / F03_2014), the correct mapping is NEGOTIATED_WITH_COMPETITION.
# Code "Z" ("Not specified") has no R2.0.9 equivalent, mapped to None (same as authority type).
_PROCEDURE_TYPE_CODE_MAP: dict[str, str | None] = {
    "1": "OPEN",
    "2": "RESTRICTED",
    "3": "ACCELERATED_RESTRICTED",
    "4": "NEGOTIATED_WITH_COMPETITION",
    "6": "ACCELERATED_NEGOTIATED",
    "B": "COMPETITIVE_NEGOTIATION",
    "C": "COMPETITIVE_DIALOGUE",
    "G": "INNOVATION_PARTNERSHIP",
    "T": "AWARD_CONTRACT_WITHOUT_CALL",
    "V": "AWARD_CONTRACT_WITHOUT_CALL",
    "Z": None,
}

# Human-readable descriptions for procedure type codes, from TED schema documentation
_PROCEDURE_TYPE_DESCRIPTIONS: dict[str, str] = {
    "OPEN": "Open procedure",
    "RESTRICTED": "Restricted procedure",
    "ACCELERATED_RESTRICTED": "Accelerated restricted procedure",
    "NEGOTIATED_WITH_COMPETITION": "Negotiated with prior call for competition",
    "ACCELERATED_NEGOTIATED": "Accelerated negotiated procedure",
    "COMPETITIVE_NEGOTIATION": "Competitive procedure with negotiation",
    "COMPETITIVE_DIALOGUE": "Competitive dialogue",
    "INNOVATION_PARTNERSHIP": "Innovation partnership",
    "AWARD_CONTRACT_WITHOUT_CALL": "Negotiated without a prior call for competition",
}


def _normalize_procedure_type(
    raw_code: Optional[str], description: Optional[str]
) -> Optional[ProcedureTypeEntry]:
    """Convert a raw procedure type code to a normalized ProcedureTypeEntry.

    For R2.0.9, raw_code is already canonical (e.g. "OPEN").
    For R2.0.7/R2.0.8, raw_code is a numeric/letter code (e.g. "1") that
    gets mapped to the canonical form.
    For eForms, raw_code is lowercase (e.g. "open") and gets uppercased.
    """
    if raw_code is None:
        return None

    # Check if it's an old-style code that needs mapping
    if raw_code in _PROCEDURE_TYPE_CODE_MAP:
        canonical = _PROCEDURE_TYPE_CODE_MAP[raw_code]
        if canonical is None:
            return None
        return ProcedureTypeEntry(
            code=canonical,
            description=_PROCEDURE_TYPE_DESCRIPTIONS.get(canonical),
        )

    # Uppercase for eForms compatibility, then use canonical description if available
    code = raw_code.upper()
    return ProcedureTypeEntry(
        code=code,
        description=description or _PROCEDURE_TYPE_DESCRIPTIONS.get(code),
    )


logger = logging.getLogger(__name__)


def _default_ns(elem: etree._Element) -> str:
    """Get the default namespace wrapped in braces for use in find/findall."""
    ns = elem.nsmap.get(None)
    return f"{{{ns}}}" if ns else ""


def _parse_date_yyyymmdd(text: Optional[str]) -> Optional[date]:
    """
    Parse date from YYYYMMDD format (e.g., "20110104").

    Used for: DATE_PUB, DS_DATE_DISPATCH, DELETION_DATE
    """
    if not text:
        return None

    stripped = text.strip()
    if not stripped:
        return None

    # Must be exactly 8 digits
    if not re.match(r"^\d{8}$", stripped):
        return None

    year = int(stripped[0:4])
    month = int(stripped[4:6])
    day = int(stripped[6:8])

    try:
        return date(year, month, day)
    except ValueError:
        return None


def _parse_optional_int(text: Optional[str], field_name: str) -> Optional[int]:
    """Parse an optional integer field, returning None for invalid values.

    For optional fields, malformed data (e.g., text where a number is expected)
    is treated as missing data. Logs a warning for visibility into data quality.
    """
    if text is None:
        return None
    text = text.strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        logger.warning(
            "Invalid integer value for %s: %r (expected numeric value)",
            field_name,
            text,
        )
        return None


def parse_xml_file(xml_file: Path) -> Optional[List[TedAwardDataModel]]:
    """Parse TED 2.0 XML file and return structured data."""
    try:
        tree = etree.parse(xml_file)
        root = tree.getroot()

        variant = _detect_variant(root)
        logger.debug(f"Processing {xml_file.name} as {variant}")

        document = _extract_document_info(root, xml_file, variant)
        if not document:
            return None

        contracting_body, contact_fields = _extract_contracting_body(root, variant)
        if not contracting_body:
            logger.debug(f"No contracting body found in {xml_file.name}")
            return None

        # Add contact fields to document
        document = document.model_copy(update=contact_fields)

        contract = _extract_contract_info(root, variant)
        if not contract:
            logger.debug(f"No contract info found in {xml_file.name}")
            return None

        awards = _extract_awards(root, variant)
        if not awards:
            logger.debug(f"No awards found in {xml_file.name}")
            return None

        return [
            TedAwardDataModel(
                document=document,
                contracting_body=contracting_body,
                contract=contract,
                awards=awards,
            )
        ]

    except Exception as e:
        logger.error(f"Error parsing TED 2.0 file {xml_file}: {e}")
        raise


def _detect_variant(root: etree._Element) -> str:
    """Detect which TED 2.0 variant this is based on XML structure."""
    # Check schema location for version
    schema_location = root.get(
        "{http://www.w3.org/2001/XMLSchema-instance}schemaLocation", ""
    )

    if "R2.0.9" in schema_location:
        return "R2.0.9"
    elif "R2.0.8" in schema_location:
        return "R2.0.8"
    elif "R2.0.7" in schema_location:
        return "R2.0.7"

    # Fall back to structural detection
    if (
        root.find(".//{http://publications.europa.eu/TED_schema/Export}F03_2014")
        is not None
    ):
        return "R2.0.9"
    elif (
        root.find(".//{http://publications.europa.eu/TED_schema/Export}CONTRACT_AWARD")
        is not None
    ):
        return "R2.0.7/R2.0.8"

    return "Unknown"


def _extract_document_info(
    root: etree._Element, xml_file: Path, variant: str
) -> Optional[DocumentModel]:
    """Extract document-level information."""
    ns = _default_ns(root)

    # Extract document ID from DOC_ID attribute or filename
    doc_id = root.get("DOC_ID")
    if not doc_id:
        doc_id = xml_file.stem.replace("_", "-")

    # Extract edition from root element
    edition = root.get("EDITION")
    if not edition:
        logger.debug(f"No edition found in {xml_file.name}")
        return None

    # Extract publication date (required)
    pub_date_elem = root.find(f".//{ns}DATE_PUB")
    if pub_date_elem is None or not pub_date_elem.text:
        logger.debug(f"No publication date found in {xml_file.name}")
        return None

    pub_date = _parse_date_yyyymmdd(pub_date_elem.text)
    if pub_date is None:
        logger.debug(f"Could not parse publication date in {xml_file.name}")
        return None

    # Extract dispatch date (optional)
    dispatch_date_elem = root.find(f".//{ns}DS_DATE_DISPATCH")
    dispatch_date = None
    if dispatch_date_elem is not None and dispatch_date_elem.text:
        dispatch_date = _parse_date_yyyymmdd(dispatch_date_elem.text)

    # Extract other document metadata
    return DocumentModel(
        doc_id=doc_id,
        edition=edition,
        publication_date=pub_date,
        dispatch_date=dispatch_date,
        reception_id=elem_text(root.find(f".//{ns}RECEPTION_ID")),
        official_journal_ref=elem_text(root.find(f".//{ns}NO_DOC_OJS")),
        source_country=elem_attr(root.find(f".//{ns}ISO_COUNTRY"), "VALUE"),
        version=variant,
    )


def _make_authority_type_entry(
    raw_code: Optional[str],
) -> Optional[AuthorityTypeEntry]:
    """Convert a raw authority type code to a normalized AuthorityTypeEntry.

    For R2.0.9, raw_code is already canonical (e.g. "BODY_PUBLIC").
    For R2.0.7/R2.0.8, raw_code is a numeric/letter code (e.g. "6") that
    gets mapped to the canonical form.
    """
    if raw_code is None:
        return None

    # Check if it's an old-style code that needs mapping
    if raw_code in _AUTHORITY_TYPE_CODE_MAP:
        canonical = _AUTHORITY_TYPE_CODE_MAP[raw_code]
        if canonical is None:
            return None
        return AuthorityTypeEntry(
            code=canonical,
            description=_AUTHORITY_TYPE_DESCRIPTIONS.get(canonical),
        )

    # Already a canonical code (R2.0.9)
    return AuthorityTypeEntry(
        code=raw_code,
        description=_AUTHORITY_TYPE_DESCRIPTIONS.get(raw_code),
    )


def _extract_contracting_body(
    root: etree._Element, variant: str
) -> tuple[Optional[ContractingBodyModel], dict]:
    """Extract contracting body information based on variant.

    Returns a tuple of (contracting_body, contact_fields_dict).
    Contact fields belong on the document, not the contracting body.
    """
    if variant == "R2.0.9":
        return _extract_contracting_body_r209(root)
    else:
        return _extract_contracting_body_r207(root)


def _extract_contracting_body_r207(
    root: etree._Element,
) -> tuple[Optional[ContractingBodyModel], dict]:
    """Extract contracting body for R2.0.7/R2.0.8 formats.

    Returns (contracting_body, contact_fields_dict).
    """
    ca_elem = root.find(
        ".//{http://publications.europa.eu/TED_schema/Export}CA_CE_CONCESSIONAIRE_PROFILE"
    )
    if ca_elem is None:
        return None, {}

    # Extract organization name - handle both R2.0.7 and R2.0.8 structures
    org_elem = ca_elem.find(
        ".//{http://publications.europa.eu/TED_schema/Export}ORGANISATION"
    )
    official_name = ""
    if org_elem is not None:
        officialname_elem = org_elem.find(
            ".//{http://publications.europa.eu/TED_schema/Export}OFFICIALNAME"
        )
        if officialname_elem is not None and officialname_elem.text:
            official_name = officialname_elem.text
        elif org_elem.text:
            official_name = org_elem.text

    address_elem = ca_elem.find(
        ".//{http://publications.europa.eu/TED_schema/Export}ADDRESS"
    )
    town_elem = ca_elem.find(".//{http://publications.europa.eu/TED_schema/Export}TOWN")
    postal_code_elem = ca_elem.find(
        ".//{http://publications.europa.eu/TED_schema/Export}POSTAL_CODE"
    )
    country_elem = ca_elem.find(
        ".//{http://publications.europa.eu/TED_schema/Export}COUNTRY"
    )
    phone_elem = ca_elem.find(
        ".//{http://publications.europa.eu/TED_schema/Export}PHONE"
    )
    email_elem = ca_elem.find(
        ".//{http://publications.europa.eu/TED_schema/Export}E_MAIL"
    )

    # Extract URL from various possible locations
    url_general_elem = root.find(
        ".//{http://publications.europa.eu/TED_schema/Export}URL_GENERAL"
    )
    url_buyer_elem = root.find(
        ".//{http://publications.europa.eu/TED_schema/Export}URL_BUYER"
    )

    # Extract authority type and activity codes from coded data section
    authority_type_elem = root.find(
        ".//{http://publications.europa.eu/TED_schema/Export}AA_AUTHORITY_TYPE"
    )
    activity_elem = root.find(
        ".//{http://publications.europa.eu/TED_schema/Export}MA_MAIN_ACTIVITIES"
    )

    contact_fields = {
        "phone": elem_text(phone_elem),
        "email": elem_text(email_elem),
        "url_general": elem_text(url_general_elem),
        "url_buyer": elem_text(url_buyer_elem),
    }

    cb = ContractingBodyModel(
        official_name=official_name,
        address=elem_text(address_elem),
        town=elem_text(town_elem),
        postal_code=elem_text(postal_code_elem),
        country_code=elem_attr(country_elem, "VALUE"),
        nuts_code=None,
        authority_type=_make_authority_type_entry(
            elem_attr(authority_type_elem, "CODE")
        ),
        main_activity_code=elem_attr(activity_elem, "CODE"),
    )

    return cb, contact_fields


def _extract_contracting_body_r209(
    root: etree._Element,
) -> tuple[Optional[ContractingBodyModel], dict]:
    """Extract contracting body for R2.0.9 format.

    Returns (contracting_body, contact_fields_dict).
    """
    ns = _default_ns(root)
    ca_elem = root.find(f".//{ns}F03_2014//{ns}CONTRACTING_BODY")
    if ca_elem is None:
        return None, {}

    # NUTS code from ADDRESS_CONTRACTING_BODY
    addr_cb_elem = ca_elem.find(f".//{ns}ADDRESS_CONTRACTING_BODY")
    nuts_code = None
    if addr_cb_elem is not None:
        nuts_elem = addr_cb_elem.find(".//{*}NUTS")
        nuts_code = nuts_elem.get("CODE") if nuts_elem is not None else None

    contact_fields = {
        "contact_point": elem_text(ca_elem.find(f".//{ns}CONTACT_POINT")),
        "phone": elem_text(ca_elem.find(f".//{ns}PHONE")),
        "email": elem_text(ca_elem.find(f".//{ns}E_MAIL")),
        "url_general": elem_text(ca_elem.find(f".//{ns}URL_GENERAL")),
        "url_buyer": elem_text(ca_elem.find(f".//{ns}URL_BUYER")),
    }

    cb = ContractingBodyModel(
        official_name=elem_text(ca_elem.find(f".//{ns}OFFICIALNAME")) or "",
        address=elem_text(ca_elem.find(f".//{ns}ADDRESS")),
        town=elem_text(ca_elem.find(f".//{ns}TOWN")),
        postal_code=elem_text(ca_elem.find(f".//{ns}POSTAL_CODE")),
        country_code=elem_attr(ca_elem.find(f".//{ns}COUNTRY"), "VALUE"),
        nuts_code=nuts_code,
        authority_type=_make_authority_type_entry(
            elem_attr(ca_elem.find(f".//{ns}CA_TYPE"), "VALUE")
        ),
        main_activity_code=elem_attr(ca_elem.find(f".//{ns}CA_ACTIVITY"), "VALUE"),
    )

    return cb, contact_fields


def _extract_contract_info(
    root: etree._Element, variant: str
) -> Optional[ContractModel]:
    """Extract contract information based on variant."""
    if variant == "R2.0.9":
        return _extract_contract_info_r209(root)
    else:
        return _extract_contract_info_r207(root)


def _build_cpv_description_map(root: etree._Element) -> dict[str, str]:
    """Build a map of CPV code -> description from CODED_DATA_SECTION/ORIGINAL_CPV."""
    ns = _default_ns(root)
    desc_map = {}
    for elem in root.iter(f"{ns}ORIGINAL_CPV"):
        code = elem.get("CODE")
        text = elem.text
        if code and text:
            desc_map[code] = text.strip()
    return desc_map


def _extract_contract_info_r207(root: etree._Element) -> Optional[ContractModel]:
    """Extract contract info for R2.0.7/R2.0.8 formats."""
    title_elem = root.find(
        ".//{http://publications.europa.eu/TED_schema/Export}TITLE_CONTRACT"
    )
    description_elem = root.find(
        ".//{http://publications.europa.eu/TED_schema/Export}SHORT_CONTRACT_DESCRIPTION"
    )

    cpv_main_elem = root.find(
        ".//{http://publications.europa.eu/TED_schema/Export}CPV_MAIN"
        "//{http://publications.europa.eu/TED_schema/Export}CPV_CODE"
    )

    # Additional CPV codes
    cpv_additional_elems = root.findall(
        ".//{http://publications.europa.eu/TED_schema/Export}CPV_ADDITIONAL"
        "//{http://publications.europa.eu/TED_schema/Export}CPV_CODE"
    )

    nature_elem = root.find(
        ".//{http://publications.europa.eu/TED_schema/Export}NC_CONTRACT_NATURE"
    )
    procedure_elem = root.find(
        ".//{http://publications.europa.eu/TED_schema/Export}PR_PROC"
    )

    # Performance location NUTS
    location_nuts_elem = root.find(
        ".//{http://publications.europa.eu/TED_schema/Export}LOCATION_NUTS"
        "//{http://publications.europa.eu/TED_schema/Export}NUTS"
    )
    nuts_code = (
        elem_attr(location_nuts_elem, "CODE")
        if location_nuts_elem is not None
        else None
    )

    # Build CPV codes list with descriptions
    cpv_desc_map = _build_cpv_description_map(root)
    cpv_codes: list[CpvCodeEntry] = []

    main_code = elem_attr(cpv_main_elem, "CODE")
    if main_code:
        cpv_codes.append(
            CpvCodeEntry(
                code=main_code,
                description=cpv_desc_map.get(main_code),
            )
        )

    for additional_elem in cpv_additional_elems:
        additional_code = additional_elem.get("CODE")
        if additional_code:
            cpv_codes.append(
                CpvCodeEntry(
                    code=additional_code,
                    description=cpv_desc_map.get(additional_code),
                )
            )

    procedure_code = elem_attr(procedure_elem, "CODE")
    procedure_description = elem_text(procedure_elem)
    if procedure_description:
        procedure_description = procedure_description.strip()
    procedure_type = _normalize_procedure_type(
        procedure_code, procedure_description or None
    )

    return ContractModel(
        title=element_text(title_elem) or "",
        short_description=element_text(description_elem),
        main_cpv_code=main_code,
        cpv_codes=cpv_codes,
        nuts_code=nuts_code,
        contract_nature_code=_normalize_contract_nature_code(
            elem_attr(nature_elem, "CODE")
        ),
        procedure_type=procedure_type,
    )


def _extract_contract_info_r209(root: etree._Element) -> Optional[ContractModel]:
    """Extract contract info for R2.0.9 format."""
    ns = _default_ns(root)
    object_elem = root.find(f".//{ns}F03_2014//{ns}OBJECT_CONTRACT")
    if object_elem is None:
        return None

    title_elem = object_elem.find(f".//{ns}TITLE")
    description_elem = object_elem.find(f".//{ns}SHORT_DESCR")
    cpv_main_elem = object_elem.find(f".//{ns}CPV_MAIN//{ns}CPV_CODE")
    type_contract_elem = object_elem.find(f".//{ns}TYPE_CONTRACT")

    # Procedure type from CODED_DATA_SECTION (same location as R2.0.7/R2.0.8)
    procedure_elem = root.find(f".//{ns}PR_PROC")

    # Performance location NUTS from OBJECT_DESCR
    nuts_elem = object_elem.find(f".//{ns}OBJECT_DESCR//{{*}}NUTS")
    nuts_code = nuts_elem.get("CODE") if nuts_elem is not None else None

    # Build CPV codes list with descriptions
    cpv_desc_map = _build_cpv_description_map(root)
    cpv_codes: list[CpvCodeEntry] = []

    main_code = None
    if cpv_main_elem is not None:
        main_code = cpv_main_elem.get("CODE")
        if main_code:
            cpv_codes.append(
                CpvCodeEntry(
                    code=main_code,
                    description=cpv_desc_map.get(main_code),
                )
            )

    procedure_code = elem_attr(procedure_elem, "CODE")
    procedure_description = elem_text(procedure_elem)
    if procedure_description:
        procedure_description = procedure_description.strip()
    procedure_type = _normalize_procedure_type(
        procedure_code, procedure_description or None
    )

    return ContractModel(
        title=element_text(title_elem) or "",
        short_description=element_text(description_elem),
        main_cpv_code=main_code,
        cpv_codes=cpv_codes,
        nuts_code=nuts_code,
        contract_nature_code=_normalize_contract_nature_code(
            type_contract_elem.get("CTYPE") if type_contract_elem is not None else None
        ),
        procedure_type=procedure_type,
    )


def _extract_awards(root: etree._Element, variant: str) -> List[AwardModel]:
    """Extract award information based on variant."""
    if variant == "R2.0.9":
        return _extract_awards_r209(root)
    else:
        return _extract_awards_r207(root)


def _extract_awards_r207(root: etree._Element) -> List[AwardModel]:
    """Extract awards for R2.0.7/R2.0.8 formats."""
    awards = []

    award_elems = root.findall(
        ".//{http://publications.europa.eu/TED_schema/Export}AWARD_OF_CONTRACT"
    )

    ns = "{http://publications.europa.eu/TED_schema/Export}"

    for award_elem in award_elems:
        # Skip empty AWARD_OF_CONTRACT placeholder elements.
        # In R2.0.7/R2.0.8, non-awarded lots appear as empty elements
        # or with only boilerplate (e.g. MORE_INFORMATION_TO_SUB_CONTRACTED).
        if (
            award_elem.find(f".//{ns}ECONOMIC_OPERATOR_NAME_ADDRESS") is None
            and award_elem.find(f".//{ns}CONTRACT_VALUE_INFORMATION") is None
            and award_elem.find(f".//{ns}CONTRACT_NUMBER") is None
            and award_elem.find(f".//{ns}CONTRACT_AWARD_DATE") is None
        ):
            continue

        contract_number_elem = award_elem.find(f".//{ns}CONTRACT_NUMBER")
        title_elem = award_elem.find(f".//{ns}CONTRACT_TITLE")

        value_elem = award_elem.find(
            f".//{ns}CONTRACT_VALUE_INFORMATION"
            f"//{ns}COSTS_RANGE_AND_CURRENCY_WITH_VAT_RATE"
            f"//{ns}VALUE_COST"
        )
        currency_elem = award_elem.find(
            f".//{ns}CONTRACT_VALUE_INFORMATION"
            f"//{ns}COSTS_RANGE_AND_CURRENCY_WITH_VAT_RATE"
        )

        offers_elem = award_elem.find(f".//{ns}OFFERS_RECEIVED_NUMBER")

        contractors = _extract_contractors_r207(award_elem)

        awards.append(
            AwardModel(
                contract_number=elem_text(contract_number_elem),
                award_title=element_text(title_elem),
                awarded_value=_extract_value_amount(value_elem),
                awarded_value_currency=elem_attr(currency_elem, "CURRENCY"),
                tenders_received=_parse_optional_int(
                    elem_text(offers_elem),
                    "tenders_received",
                ),
                contractors=contractors,
            )
        )

    return awards


def _extract_awards_r209(root: etree._Element) -> List[AwardModel]:
    """Extract awards for R2.0.9 format."""
    ns = _default_ns(root)
    awards = []

    for award_elem in root.findall(f".//{ns}F03_2014//{ns}AWARD_CONTRACT"):
        award_decision_elem = award_elem.find(f".//{ns}AWARDED_CONTRACT")
        if award_decision_elem is None:
            continue

        value_elem = award_decision_elem.find(f".//{ns}VAL_TOTAL")
        offers_elem = award_decision_elem.find(f".//{ns}NB_TENDERS_RECEIVED")

        contractors = _extract_contractors_r209(award_decision_elem)

        awards.append(
            AwardModel(
                contract_number=elem_text(award_elem.find(f".//{ns}CONTRACT_NO")),
                award_title=element_text(award_elem.find(f".//{ns}TITLE")),
                awarded_value=_extract_value_amount(value_elem),
                awarded_value_currency=(
                    value_elem.get("CURRENCY") if value_elem is not None else None
                ),
                tenders_received=_parse_optional_int(
                    offers_elem.text if offers_elem is not None else None,
                    "tenders_received",
                ),
                contractors=contractors,
            )
        )

    return awards


def _extract_contractors_r207(award_elem: etree._Element) -> List[ContractorModel]:
    """Extract contractor information for R2.0.7/R2.0.8."""
    contractors = []

    contractor_elems = award_elem.findall(
        ".//{http://publications.europa.eu/TED_schema/Export}ECONOMIC_OPERATOR_NAME_ADDRESS"
    )

    for contractor_elem in contractor_elems:
        contact_data_elem = contractor_elem.find(
            ".//{http://publications.europa.eu/TED_schema/Export}CONTACT_DATA_WITHOUT_RESPONSIBLE_NAME"
        )
        if contact_data_elem is None:
            continue

        # Extract organization name
        org_elem = contact_data_elem.find(
            ".//{http://publications.europa.eu/TED_schema/Export}ORGANISATION"
        )
        official_name = ""
        if org_elem is not None:
            officialname_elem = org_elem.find(
                ".//{http://publications.europa.eu/TED_schema/Export}OFFICIALNAME"
            )
            if officialname_elem is not None and officialname_elem.text:
                official_name = officialname_elem.text
            elif org_elem.text:
                official_name = org_elem.text

        address_elem = contact_data_elem.find(
            ".//{http://publications.europa.eu/TED_schema/Export}ADDRESS"
        )
        town_elem = contact_data_elem.find(
            ".//{http://publications.europa.eu/TED_schema/Export}TOWN"
        )
        postal_code_elem = contact_data_elem.find(
            ".//{http://publications.europa.eu/TED_schema/Export}POSTAL_CODE"
        )
        country_elem = contact_data_elem.find(
            ".//{http://publications.europa.eu/TED_schema/Export}COUNTRY"
        )

        contractors.append(
            ContractorModel(
                official_name=official_name,
                address=elem_text(address_elem),
                town=elem_text(town_elem),
                postal_code=elem_text(postal_code_elem),
                country_code=elem_attr(country_elem, "VALUE"),
                nuts_code=None,
            )
        )

    return contractors


def _extract_contractors_r209(award_elem: etree._Element) -> List[ContractorModel]:
    """Extract contractor information for R2.0.9."""
    ns = _default_ns(award_elem)
    contractors = []

    for contractor_elem in award_elem.findall(f".//{ns}CONTRACTOR"):
        nuts_elem = contractor_elem.find(".//{*}NUTS")

        contractors.append(
            ContractorModel(
                official_name=elem_text(contractor_elem.find(f".//{ns}OFFICIALNAME"))
                or "",
                address=elem_text(contractor_elem.find(f".//{ns}ADDRESS")),
                town=elem_text(contractor_elem.find(f".//{ns}TOWN")),
                postal_code=elem_text(contractor_elem.find(f".//{ns}POSTAL_CODE")),
                country_code=elem_attr(
                    contractor_elem.find(f".//{ns}COUNTRY"), "VALUE"
                ),
                nuts_code=nuts_elem.get("CODE") if nuts_elem is not None else None,
            )
        )

    return contractors


def _extract_value_amount(value_elem: Optional[etree._Element]) -> Optional[float]:
    """Extract value amount from element text content.

    Works for both R2.0.7/R2.0.8 (VALUE_COST) and R2.0.9 (VAL_TOTAL).
    Uses strict monetary parsers - warns and returns None for unparseable formats.
    """
    if value_elem is None:
        return None

    text_content = value_elem.text
    if not text_content:
        return None

    return parse_monetary_value(text_content, "awarded_value")
