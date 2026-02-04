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
    AwardModel,
    ContractorModel,
)
from .monetary import parse_monetary_value
from .xml import (
    first_text,
    first_attr,
    elem_text,
    elem_attr,
    element_text,
)

logger = logging.getLogger(__name__)


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


FORMAT_NAME = "TED 2.0"


def can_parse(xml_file: Path) -> bool:
    """Check if this file uses any TED 2.0 format variant."""
    try:
        tree = etree.parse(xml_file)
        root = tree.getroot()

        # Check for TED_EXPORT root element (namespace-agnostic check)
        if not root.tag.endswith("}TED_EXPORT") and root.tag != "TED_EXPORT":
            return False

        # Check if it's document type 7 (Contract award)
        doc_type = root.xpath('.//*[local-name()="TD_DOCUMENT_TYPE"][@CODE="7"]')
        if not doc_type:
            return False

        # Must have either CONTRACT_AWARD (R2.0.7/R2.0.8) or F03_2014 (R2.0.9) form
        has_contract_award = len(root.xpath('.//*[local-name()="CONTRACT_AWARD"]')) > 0
        has_f03_2014 = len(root.xpath('.//*[local-name()="F03_2014"]')) > 0

        return has_contract_award or has_f03_2014

    except Exception as e:
        logger.debug(f"Error checking if {xml_file.name} is TED 2.0 format: {e}")
        return False


def get_format_name() -> str:
    """Return the format name for this parser."""
    return FORMAT_NAME


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

        contracting_body = _extract_contracting_body(root, variant)
        if not contracting_body:
            logger.debug(f"No contracting body found in {xml_file.name}")
            return None

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
    pub_date_elems = root.xpath('.//*[local-name()="DATE_PUB"]')
    if not pub_date_elems or not pub_date_elems[0].text:
        logger.debug(f"No publication date found in {xml_file.name}")
        return None

    pub_date = _parse_date_yyyymmdd(pub_date_elems[0].text)
    if pub_date is None:
        logger.debug(f"Could not parse publication date in {xml_file.name}")
        return None

    # Extract dispatch date (optional)
    dispatch_date_elems = root.xpath('.//*[local-name()="DS_DATE_DISPATCH"]')
    dispatch_date = None
    if dispatch_date_elems and dispatch_date_elems[0].text:
        dispatch_date = _parse_date_yyyymmdd(dispatch_date_elems[0].text)

    # Extract other document metadata
    reception_id_elems = root.xpath('.//*[local-name()="RECEPTION_ID"]')
    no_doc_oj_elems = root.xpath('.//*[local-name()="NO_DOC_OJS"]')
    country_elems = root.xpath('.//*[local-name()="ISO_COUNTRY"]')

    return DocumentModel(
        doc_id=doc_id,
        edition=edition,
        publication_date=pub_date,
        dispatch_date=dispatch_date,
        reception_id=first_text(reception_id_elems),
        official_journal_ref=first_text(no_doc_oj_elems),
        source_country=first_attr(country_elems, "VALUE"),
        version=variant,
    )


def _extract_contracting_body(
    root: etree._Element, variant: str
) -> Optional[ContractingBodyModel]:
    """Extract contracting body information based on variant."""
    if variant == "R2.0.9":
        return _extract_contracting_body_r209(root)
    else:
        return _extract_contracting_body_r207(root)


def _extract_contracting_body_r207(
    root: etree._Element,
) -> Optional[ContractingBodyModel]:
    """Extract contracting body for R2.0.7/R2.0.8 formats."""
    ca_elem = root.find(
        ".//{http://publications.europa.eu/TED_schema/Export}CA_CE_CONCESSIONAIRE_PROFILE"
    )
    if ca_elem is None:
        return None

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

    return ContractingBodyModel(
        official_name=official_name,
        address=elem_text(address_elem),
        town=elem_text(town_elem),
        postal_code=elem_text(postal_code_elem),
        country_code=elem_attr(country_elem, "VALUE"),
        contact_point=None,
        phone=elem_text(phone_elem),
        email=elem_text(email_elem),
        url_general=elem_text(url_general_elem),
        url_buyer=elem_text(url_buyer_elem),
        authority_type_code=elem_attr(authority_type_elem, "CODE"),
        main_activity_code=elem_attr(activity_elem, "CODE"),
    )


def _extract_contracting_body_r209(
    root: etree._Element,
) -> Optional[ContractingBodyModel]:
    """Extract contracting body for R2.0.9 format."""
    ca_elems = root.xpath(
        './/*[local-name()="F03_2014"]//*[local-name()="CONTRACTING_BODY"]'
    )
    if not ca_elems:
        return None

    ca_elem = ca_elems[0]

    name_elems = ca_elem.xpath('.//*[local-name()="OFFICIALNAME"]')
    address_elems = ca_elem.xpath('.//*[local-name()="ADDRESS"]')
    town_elems = ca_elem.xpath('.//*[local-name()="TOWN"]')
    postal_code_elems = ca_elem.xpath('.//*[local-name()="POSTAL_CODE"]')
    country_elems = ca_elem.xpath('.//*[local-name()="COUNTRY"]')
    contact_elems = ca_elem.xpath('.//*[local-name()="CONTACT_POINT"]')
    phone_elems = ca_elem.xpath('.//*[local-name()="PHONE"]')
    email_elems = ca_elem.xpath('.//*[local-name()="E_MAIL"]')
    url_general_elems = ca_elem.xpath('.//*[local-name()="URL_GENERAL"]')
    url_buyer_elems = ca_elem.xpath('.//*[local-name()="URL_BUYER"]')
    authority_type_elems = ca_elem.xpath('.//*[local-name()="CA_TYPE"]')
    activity_elems = ca_elem.xpath('.//*[local-name()="CA_ACTIVITY"]')

    return ContractingBodyModel(
        official_name=first_text(name_elems) or "",
        address=first_text(address_elems),
        town=first_text(town_elems),
        postal_code=first_text(postal_code_elems),
        country_code=first_attr(country_elems, "VALUE"),
        contact_point=first_text(contact_elems),
        phone=first_text(phone_elems),
        email=first_text(email_elems),
        url_general=first_text(url_general_elems),
        url_buyer=first_text(url_buyer_elems),
        authority_type_code=first_attr(authority_type_elems, "VALUE"),
        main_activity_code=first_attr(activity_elems, "VALUE"),
    )


def _extract_contract_info(
    root: etree._Element, variant: str
) -> Optional[ContractModel]:
    """Extract contract information based on variant."""
    if variant == "R2.0.9":
        return _extract_contract_info_r209(root)
    else:
        return _extract_contract_info_r207(root)


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

    nature_elem = root.find(
        ".//{http://publications.europa.eu/TED_schema/Export}NC_CONTRACT_NATURE"
    )
    procedure_elem = root.find(
        ".//{http://publications.europa.eu/TED_schema/Export}PR_PROC"
    )

    return ContractModel(
        title=element_text(title_elem) or "",
        short_description=element_text(description_elem),
        main_cpv_code=elem_attr(cpv_main_elem, "CODE"),
        contract_nature_code=elem_attr(nature_elem, "CODE"),
        procedure_type_code=elem_attr(procedure_elem, "CODE"),
    )


def _extract_contract_info_r209(root: etree._Element) -> Optional[ContractModel]:
    """Extract contract info for R2.0.9 format."""
    object_elems = root.xpath(
        './/*[local-name()="F03_2014"]//*[local-name()="OBJECT_CONTRACT"]'
    )
    if not object_elems:
        return None

    object_elem = object_elems[0]

    title_elems = object_elem.xpath('.//*[local-name()="TITLE"]')
    description_elems = object_elem.xpath('.//*[local-name()="SHORT_DESCR"]')
    cpv_main_elems = object_elem.xpath(
        './/*[local-name()="CPV_MAIN"]//*[local-name()="CPV_CODE"]'
    )
    type_contract_elems = object_elem.xpath('.//*[local-name()="TYPE_CONTRACT"]')

    return ContractModel(
        title=element_text(title_elems[0]) if title_elems else "",
        short_description=(
            element_text(description_elems[0]) if description_elems else None
        ),
        main_cpv_code=cpv_main_elems[0].get("CODE") if cpv_main_elems else None,
        contract_nature_code=(
            type_contract_elems[0].get("CTYPE") if type_contract_elems else None
        ),
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

    for award_elem in award_elems:
        contract_number_elem = award_elem.find(
            ".//{http://publications.europa.eu/TED_schema/Export}CONTRACT_NUMBER"
        )
        title_elem = award_elem.find(
            ".//{http://publications.europa.eu/TED_schema/Export}CONTRACT_TITLE"
        )

        value_elem = award_elem.find(
            ".//{http://publications.europa.eu/TED_schema/Export}CONTRACT_VALUE_INFORMATION"
            "//{http://publications.europa.eu/TED_schema/Export}COSTS_RANGE_AND_CURRENCY_WITH_VAT_RATE"
            "//{http://publications.europa.eu/TED_schema/Export}VALUE_COST"
        )
        currency_elem = award_elem.find(
            ".//{http://publications.europa.eu/TED_schema/Export}CONTRACT_VALUE_INFORMATION"
            "//{http://publications.europa.eu/TED_schema/Export}COSTS_RANGE_AND_CURRENCY_WITH_VAT_RATE"
        )

        offers_elem = award_elem.find(
            ".//{http://publications.europa.eu/TED_schema/Export}OFFERS_RECEIVED_NUMBER"
        )

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
    awards = []

    award_elems = root.xpath(
        './/*[local-name()="F03_2014"]//*[local-name()="AWARD_CONTRACT"]'
    )

    for award_elem in award_elems:
        contract_number_elems = award_elem.xpath('.//*[local-name()="CONTRACT_NO"]')
        title_elems = award_elem.xpath('.//*[local-name()="TITLE"]')

        award_decision_elems = award_elem.xpath('.//*[local-name()="AWARDED_CONTRACT"]')
        if not award_decision_elems:
            continue

        award_decision_elem = award_decision_elems[0]

        value_elems = award_decision_elem.xpath('.//*[local-name()="VAL_TOTAL"]')
        offers_elems = award_decision_elem.xpath(
            './/*[local-name()="NB_TENDERS_RECEIVED"]'
        )

        contractors = _extract_contractors_r209(award_decision_elem)

        awards.append(
            AwardModel(
                contract_number=first_text(contract_number_elems),
                award_title=element_text(title_elems[0]) if title_elems else None,
                awarded_value=(
                    _extract_value_amount(value_elems[0]) if value_elems else None
                ),
                awarded_value_currency=(
                    value_elems[0].get("CURRENCY") if value_elems else None
                ),
                tenders_received=_parse_optional_int(
                    offers_elems[0].text if offers_elems else None,
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
            )
        )

    return contractors


def _extract_contractors_r209(award_elem: etree._Element) -> List[ContractorModel]:
    """Extract contractor information for R2.0.9."""
    contractors = []

    contractor_elems = award_elem.xpath('.//*[local-name()="CONTRACTOR"]')

    for contractor_elem in contractor_elems:
        name_elems = contractor_elem.xpath('.//*[local-name()="OFFICIALNAME"]')
        address_elems = contractor_elem.xpath('.//*[local-name()="ADDRESS"]')
        town_elems = contractor_elem.xpath('.//*[local-name()="TOWN"]')
        postal_code_elems = contractor_elem.xpath('.//*[local-name()="POSTAL_CODE"]')
        country_elems = contractor_elem.xpath('.//*[local-name()="COUNTRY"]')

        contractors.append(
            ContractorModel(
                official_name=first_text(name_elems) or "",
                address=first_text(address_elems),
                town=first_text(town_elems),
                postal_code=first_text(postal_code_elems),
                country_code=first_attr(country_elems, "VALUE"),
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
