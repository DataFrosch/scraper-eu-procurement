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
from typing import List, NamedTuple, Optional

from lxml import etree

from ..schema import (
    AwardDataModel,
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

# Authority type normalization: exact eForms codes (buyer-legal-type codelist).
# Source: OP-TED/ted-xml-data-converter other-mappings.xml (BT-11 ca-types).
# Note: MINISTRY and NATIONAL_AGENCY both map to cga per the official converter.
# Code 8 ("Other") and Z ("Not specified") have no eForms equivalent; mapped to None.
#
# Mapping from old-style codes (R2.0.7/R2.0.8 CODED_DATA_SECTION).
# Verified empirically from R2.0.9 dual-code files.
_AUTHORITY_TYPE_CODE_MAP: dict[str, str | None] = {
    "1": "cga",
    "3": "ra",
    "5": "eu-ins-bod-ag",
    "6": "body-pl",
    "8": None,
    "N": "cga",
    "R": "body-pl-ra",
    "Z": None,
}

# Mapping from TED v2 R2.0.9 canonical codes (CA_TYPE VALUE) to eForms codes.
# Source: OP-TED/ted-xml-data-converter other-mappings.xml.
_TED_V2_AUTHORITY_TO_CANONICAL: dict[str, str | None] = {
    "MINISTRY": "cga",
    "NATIONAL_AGENCY": "cga",
    "REGIONAL_AUTHORITY": "ra",
    "REGIONAL_AGENCY": "body-pl-ra",
    "BODY_PUBLIC": "body-pl",
    "EU_INSTITUTION": "eu-ins-bod-ag",
    "OTHER": None,  # no eForms equivalent, consistent with old code "8" → None
}

# Human-readable descriptions for authority type codes
_AUTHORITY_TYPE_DESCRIPTIONS: dict[str, str] = {
    "cga": "Central government authority",
    "ra": "Regional authority",
    "eu-ins-bod-ag": "EU institution, body or agency",
    "body-pl": "Body governed by public law",
    "body-pl-cga": "Body governed by public law, controlled by a central government authority",
    "body-pl-la": "Body governed by public law, controlled by a local authority",
    "body-pl-ra": "Body governed by public law, controlled by a regional authority",
    "la": "Local authority",
    "def-cont": "Defence contractor",
    "int-org": "International organisation",
    "pub-undert": "Public undertaking",
}

# Mapping from old-style contract nature codes (R2.0.7/R2.0.8 NC_CONTRACT_NATURE CODE)
# to canonical codes (R2.0.9 TYPE_CONTRACT CTYPE). Verified empirically from F03_2014
# dual-code files containing both NC_CONTRACT_NATURE and TYPE_CONTRACT:
# "1" -> WORKS (1,961 matches), "2" -> SUPPLIES (5,049), "4" -> SERVICES (6,226).
# Contract nature codes: exact eForms codes (lowercase).
# Source: OP-TED/ted-xml-data-converter other-mappings.xml (BT-23 contract-nature-types).
_CONTRACT_NATURE_CODE_MAP: dict[str, str] = {
    "1": "works",
    "2": "supplies",
    "4": "services",
}

# Mapping from TED v2 R2.0.9 uppercase codes (TYPE_CONTRACT CTYPE) to eForms codes.
_TED_V2_CONTRACT_NATURE_TO_CANONICAL: dict[str, str] = {
    "WORKS": "works",
    "SUPPLIES": "supplies",
    "SERVICES": "services",
}

# Known eForms contract nature codes (contract-nature-types codelist).
_CONTRACT_NATURE_CODES: set[str] = {"works", "supplies", "services", "combined"}


def _normalize_contract_nature_code(raw_code: Optional[str]) -> Optional[str]:
    """Normalize a contract nature code to exact eForms form (lowercase).

    Old-style numeric codes are mapped via _CONTRACT_NATURE_CODE_MAP.
    TED v2 uppercase codes are mapped via _TED_V2_CONTRACT_NATURE_TO_CANONICAL.
    Known eForms codes pass through. Unknown codes log a warning and return None.
    """
    if raw_code is None:
        return None

    if raw_code in _CONTRACT_NATURE_CODE_MAP:
        return _CONTRACT_NATURE_CODE_MAP[raw_code]

    if raw_code in _TED_V2_CONTRACT_NATURE_TO_CANONICAL:
        return _TED_V2_CONTRACT_NATURE_TO_CANONICAL[raw_code]

    if raw_code in _CONTRACT_NATURE_CODES:
        return raw_code

    logger.warning("Unknown contract nature code: %r", raw_code)
    return None


# Procedure type normalization: exact eForms codes (procurement-procedure-type codelist).
# Source: OP-TED/ted-xml-data-converter other-mappings.xml (BT-105 procedure-types).
# In eForms, "accelerated" is a separate boolean flag (BT-106), not a procedure type.
# The converter maps ACCELERATED_PROC → BT-106=true and keeps the base procedure type.


class ProcedureMapping(NamedTuple):
    """Result of mapping a raw procedure type code to eForms."""

    code: str | None
    accelerated: bool


# Mapping from old-style procedure type codes (R2.0.7/R2.0.8 PR_PROC CODE).
# Verified empirically from F03_2014 dual-code files.
# Codes "B" (competitive negotiation) and "4" (negotiated with competition) both map
# to neg-w-call per the official converter — they were always the same thing.
_PROCEDURE_TYPE_CODE_MAP: dict[str, ProcedureMapping] = {
    "1": ProcedureMapping("open", False),
    "2": ProcedureMapping("restricted", False),
    "3": ProcedureMapping("restricted", True),
    "4": ProcedureMapping("neg-w-call", False),
    "6": ProcedureMapping("neg-w-call", True),
    "B": ProcedureMapping("neg-w-call", False),
    "C": ProcedureMapping("comp-dial", False),
    "G": ProcedureMapping("innovation", False),
    "T": ProcedureMapping("neg-wo-call", False),
    "V": ProcedureMapping("neg-wo-call", False),
    "N": ProcedureMapping(None, False),
    "Z": ProcedureMapping(None, False),
}

# Mapping from TED v2 R2.0.9 canonical codes (PT_* element names / PR_PROC CODE values)
# to eForms codes. Source: OP-TED/ted-xml-data-converter other-mappings.xml.
_TED_V2_TO_CANONICAL: dict[str, ProcedureMapping] = {
    "OPEN": ProcedureMapping("open", False),
    "RESTRICTED": ProcedureMapping("restricted", False),
    "ACCELERATED_RESTRICTED": ProcedureMapping("restricted", True),
    "COMPETITIVE_NEGOTIATION": ProcedureMapping("neg-w-call", False),
    "NEGOTIATED_WITH_COMPETITION": ProcedureMapping("neg-w-call", False),
    "ACCELERATED_NEGOTIATED": ProcedureMapping("neg-w-call", True),
    "COMPETITIVE_DIALOGUE": ProcedureMapping("comp-dial", False),
    "INNOVATION_PARTNERSHIP": ProcedureMapping("innovation", False),
    "AWARD_CONTRACT_WITHOUT_CALL": ProcedureMapping("neg-wo-call", False),
    "NEGOTIATED_WITH_PRIOR_CALL": ProcedureMapping("neg-w-call", False),
    "AWARD_CONTRACT_WITH_PRIOR_PUBLICATION": ProcedureMapping("neg-w-call", False),
    "AWARD_CONTRACT_WITHOUT_PUBLICATION": ProcedureMapping("neg-wo-call", False),
    "NEGOTIATED_WITHOUT_PUBLICATION": ProcedureMapping("neg-wo-call", False),
    "INVOLVING_NEGOTIATION": ProcedureMapping(
        None, False
    ),  # maps to UNKNOWN in converter
}

# Human-readable descriptions for procedure type codes
_PROCEDURE_TYPE_DESCRIPTIONS: dict[str, str] = {
    "open": "Open procedure",
    "restricted": "Restricted procedure",
    "neg-w-call": "Negotiated with prior call for competition",
    "comp-dial": "Competitive dialogue",
    "innovation": "Innovation partnership",
    "neg-wo-call": "Negotiated without prior call for competition",
    "oth-single": "Other single stage procedure",
    "oth-mult": "Other multiple stage procedure",
    "comp-tend": "Competitive tendering (Regulation 1370/2007)",
}


def _normalize_procedure_type(
    raw_code: Optional[str], description: Optional[str]
) -> tuple[Optional[ProcedureTypeEntry], bool]:
    """Convert a raw procedure type code to a normalized ProcedureTypeEntry.

    Returns (procedure_type_entry, accelerated) tuple.
    All codes normalize to exact eForms codes (lowercase, hyphens). Mapping chain:
    - R2.0.7/R2.0.8 numeric/letter codes (e.g. "1") → via _PROCEDURE_TYPE_CODE_MAP
    - R2.0.9 canonical codes (e.g. "AWARD_CONTRACT_WITHOUT_CALL") → via _TED_V2_TO_CANONICAL
    - eForms codes (e.g. "neg-wo-call") → pass through as-is
    """
    if raw_code is None:
        return None, False

    # Old-style numeric/letter code (R2.0.7/R2.0.8)
    if raw_code in _PROCEDURE_TYPE_CODE_MAP:
        canonical, accelerated = _PROCEDURE_TYPE_CODE_MAP[raw_code]
        if canonical is None:
            return None, False
        return ProcedureTypeEntry(
            code=canonical,
            description=_PROCEDURE_TYPE_DESCRIPTIONS.get(canonical),
        ), accelerated

    # TED v2 R2.0.9 uppercase code that needs remapping
    if raw_code in _TED_V2_TO_CANONICAL:
        canonical, accelerated = _TED_V2_TO_CANONICAL[raw_code]
        if canonical is None:
            return None, False
        return ProcedureTypeEntry(
            code=canonical,
            description=_PROCEDURE_TYPE_DESCRIPTIONS.get(canonical),
        ), accelerated

    # Known eForms code — pass through
    if raw_code in _PROCEDURE_TYPE_DESCRIPTIONS:
        return ProcedureTypeEntry(
            code=raw_code,
            description=description or _PROCEDURE_TYPE_DESCRIPTIONS[raw_code],
        ), False

    logger.warning("Unknown procedure type code: %r", raw_code)
    return None, False


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


def parse_xml_file(xml_file: Path) -> Optional[List[AwardDataModel]]:
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
            AwardDataModel(
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

    All codes normalize to exact eForms codes (lowercase, hyphens). Mapping chain:
    - R2.0.7/R2.0.8 numeric/letter codes (e.g. "6") → via _AUTHORITY_TYPE_CODE_MAP
    - R2.0.9 canonical codes (e.g. "BODY_PUBLIC") → via _TED_V2_AUTHORITY_TO_CANONICAL
    - eForms codes (e.g. "body-pl") → pass through as-is
    """
    if raw_code is None:
        return None

    # Old-style numeric/letter code (R2.0.7/R2.0.8)
    if raw_code in _AUTHORITY_TYPE_CODE_MAP:
        canonical = _AUTHORITY_TYPE_CODE_MAP[raw_code]
        if canonical is None:
            return None
        return AuthorityTypeEntry(
            code=canonical,
            description=_AUTHORITY_TYPE_DESCRIPTIONS.get(canonical),
        )

    # TED v2 R2.0.9 uppercase code that needs remapping
    if raw_code in _TED_V2_AUTHORITY_TO_CANONICAL:
        canonical = _TED_V2_AUTHORITY_TO_CANONICAL[raw_code]
        if canonical is None:
            return None
        return AuthorityTypeEntry(
            code=canonical,
            description=_AUTHORITY_TYPE_DESCRIPTIONS.get(canonical),
        )

    # Known eForms code — pass through
    if raw_code in _AUTHORITY_TYPE_DESCRIPTIONS:
        return AuthorityTypeEntry(
            code=raw_code,
            description=_AUTHORITY_TYPE_DESCRIPTIONS[raw_code],
        )

    logger.warning("Unknown authority type code: %r", raw_code)
    return None


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
    procedure_type, accelerated = _normalize_procedure_type(
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
        accelerated=accelerated,
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
    procedure_type, accelerated = _normalize_procedure_type(
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
        accelerated=accelerated,
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
