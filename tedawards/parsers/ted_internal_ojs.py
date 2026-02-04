"""
TED INTERNAL_OJS format parser for R2.0.5 (2008).
Handles the INTERNAL_OJS wrapper format with language-specific files.
"""

import logging
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
from .xml import xpath_text, parse_date_yyyymmdd, parse_monetary_value

logger = logging.getLogger(__name__)

FORMAT_NAME = "TED INTERNAL_OJS R2.0.5"


def can_parse(file_path: Path) -> bool:
    """Check if this file uses INTERNAL_OJS format."""
    try:
        # Check for .en extension (English language files only)
        if not file_path.suffix.lower() == ".en":
            return False

        tree = etree.parse(file_path)
        root = tree.getroot()

        # Check for INTERNAL_OJS root element
        if root.tag != "INTERNAL_OJS":
            return False

        # Check if it's an award notice (NAT_NOTICE = 7)
        nat_notice = root.xpath(".//BIB_DOC_S/NAT_NOTICE/text()")
        if not nat_notice or nat_notice[0] != "7":
            return False

        # Must have CONTRACT_AWARD_SUM form
        has_award_form = len(root.xpath(".//CONTRACT_AWARD_SUM")) > 0

        return has_award_form

    except Exception as e:
        logger.debug(f"Error checking if {file_path.name} is INTERNAL_OJS format: {e}")
        return False


def get_format_name() -> str:
    """Return the format name for this parser."""
    return FORMAT_NAME


def parse_xml_file(xml_file: Path) -> Optional[List[TedAwardDataModel]]:
    """Parse INTERNAL_OJS XML file and return structured data."""
    try:
        tree = etree.parse(xml_file)
        root = tree.getroot()

        document = _extract_document_info(root, xml_file)
        if not document:
            return None

        contracting_body = _extract_contracting_body(root)
        if not contracting_body:
            logger.debug(f"No contracting body found in {xml_file.name}")
            return None

        contract = _extract_contract_info(root)
        if not contract:
            logger.debug(f"No contract info found in {xml_file.name}")
            return None

        awards = _extract_awards(root)
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
        logger.error(f"Error parsing INTERNAL_OJS file {xml_file}: {e}")
        raise


def _extract_document_info(
    root: etree._Element, xml_file: Path
) -> Optional[DocumentModel]:
    """Extract document metadata from BIB_INFO section."""
    bib_info_elems = root.xpath(".//BIB_INFO")
    bib_doc_s_elems = root.xpath(".//BIB_DOC_S")

    if not bib_info_elems or not bib_doc_s_elems:
        logger.debug(f"Missing BIB_INFO or BIB_DOC_S in {xml_file.name}")
        return None

    bib_info = bib_info_elems[0]
    bib_doc_s = bib_doc_s_elems[0]

    # Extract OJS reference info
    ref_ojs_elems = bib_info.xpath(".//REF_OJS")
    if not ref_ojs_elems:
        logger.debug(f"Missing REF_OJS in {xml_file.name}")
        return None

    ref_ojs = ref_ojs_elems[0]
    no_oj = xpath_text(ref_ojs, ".//NO_OJ")
    date_pub = xpath_text(ref_ojs, ".//DATE_PUB")

    # Extract document reference (use direct child to avoid REF_NOTICE)
    no_doc_ojs_elems = bib_doc_s.xpath("./NO_DOC_OJS/text()")
    no_doc_ojs = no_doc_ojs_elems[0] if no_doc_ojs_elems else ""
    iso_country = xpath_text(bib_doc_s, "./ISO_COUNTRY")
    date_disp = xpath_text(bib_doc_s, "./DATE_DISP")

    # Parse dates
    publication_date = None
    if date_pub and len(date_pub) == 8:
        try:
            publication_date = parse_date_yyyymmdd(date_pub)
        except ValueError:
            logger.warning(f"Invalid publication date format: {date_pub}")

    dispatch_date = None
    if date_disp and len(date_disp) == 8:
        try:
            dispatch_date = parse_date_yyyymmdd(date_disp)
        except ValueError:
            logger.warning(f"Invalid dispatch date format: {date_disp}")

    # Extract deletion date from TECHNICAL_INFO
    deletion_date = None
    deletion_date_str = xpath_text(root, ".//TECHNICAL_INFO/DELETION_DATE")
    if deletion_date_str and len(deletion_date_str) == 8:
        try:
            deletion_date = parse_date_yyyymmdd(deletion_date_str)
        except ValueError:
            pass

    # Build document ID from NO_DOC_OJS
    doc_id = f"ojs-{no_doc_ojs}" if no_doc_ojs else f"ojs-{xml_file.stem}"

    return DocumentModel(
        doc_id=doc_id,
        edition=no_oj or "1",
        version="1",
        reception_id=no_doc_ojs,
        deletion_date=deletion_date,
        official_journal_ref=no_doc_ojs,
        publication_date=publication_date,
        dispatch_date=dispatch_date,
        source_country=iso_country or None,
    )


def _extract_contracting_body(root: etree._Element) -> Optional[ContractingBodyModel]:
    """Extract contracting body information."""
    # Find contracting authority in FD_CONTRACT_AWARD_SUM
    ca_profile_elems = root.xpath(
        ".//FD_CONTRACT_AWARD_SUM//CA_CE_CONCESSIONAIRE_PROFILE"
    )
    if not ca_profile_elems:
        return None

    ca_profile = ca_profile_elems[0]

    organisation = xpath_text(ca_profile, ".//ORGANISATION")
    if not organisation:
        return None

    address = xpath_text(ca_profile, ".//ADDRESS")
    town = xpath_text(ca_profile, ".//TOWN")
    postal_code = xpath_text(ca_profile, ".//POSTAL_CODE")
    country = ca_profile.xpath(".//COUNTRY/@VALUE")
    country_code = country[0] if country else None
    phone = xpath_text(ca_profile, ".//PHONE")
    email = xpath_text(ca_profile, ".//E_MAIL")
    fax = xpath_text(ca_profile, ".//FAX")

    return ContractingBodyModel(
        official_name=organisation,
        address=address or None,
        town=town or None,
        postal_code=postal_code or None,
        country_code=country_code,
        nuts_code=None,
        contact_point=None,
        phone=phone or None,
        email=email or None,
        fax=fax or None,
        url_general=None,
        url_buyer=None,
        authority_type_code=None,
        main_activity_code=None,
    )


def _extract_contract_info(root: etree._Element) -> Optional[ContractModel]:
    """Extract contract information."""
    bib_doc_s_elems = root.xpath(".//BIB_DOC_S")
    if not bib_doc_s_elems:
        return None

    bib_doc_s = bib_doc_s_elems[0]

    # Extract title from TI_DOC
    title_parts = bib_doc_s.xpath(".//TI_DOC/P/text()")
    title = title_parts[0] if title_parts else ""

    # Extract reference number (use direct child to avoid REF_NOTICE)
    no_doc_ojs_elems = bib_doc_s.xpath("./NO_DOC_OJS/text()")
    no_doc_ojs = no_doc_ojs_elems[0] if no_doc_ojs_elems else ""

    # Extract CPV code
    cpv_code = xpath_text(bib_doc_s, ".//ORIGINAL_CPV")

    # Extract description from form
    description = xpath_text(root, ".//DESCRIPTION_SUM/P")

    # Extract total value
    total_value = None
    total_currency = None
    value_elem = root.xpath(".//TOTAL_FINAL_VALUE//VALUE_COST/text()")
    if value_elem:
        total_value = parse_monetary_value(value_elem[0])
        currency_elem = root.xpath(
            ".//TOTAL_FINAL_VALUE//COSTS_RANGE_AND_CURRENCY_WITH_VAT_RATE/@CURRENCY"
        )
        total_currency = currency_elem[0] if currency_elem else None

    return ContractModel(
        title=title,
        reference_number=no_doc_ojs or None,
        short_description=description or None,
        main_cpv_code=cpv_code or None,
        contract_nature_code=None,
        total_value=total_value,
        total_value_currency=total_currency,
        procedure_type_code=None,
        award_criteria_code=None,
        performance_nuts_code=None,
    )


def _extract_awards(root: etree._Element) -> List[AwardModel]:
    """Extract award information."""
    awards = []

    # Find all AWARD_OF_CONTRACT_SUM elements
    award_elements = root.xpath(".//AWARD_OF_CONTRACT_SUM")

    if not award_elements:
        return []

    for award_elem in award_elements:
        # Extract contract number
        contract_number = xpath_text(award_elem, ".//CONTRACT_NUMBER")

        # Extract award value
        awarded_value = None
        awarded_currency = None
        value_elem = award_elem.xpath(
            ".//CONTRACT_VALUE_INFORMATION//VALUE_COST/text()"
        )
        if value_elem:
            awarded_value = parse_monetary_value(value_elem[0])
            currency_elem = award_elem.xpath(
                ".//CONTRACT_VALUE_INFORMATION//COSTS_RANGE_AND_CURRENCY_WITH_VAT_RATE/@CURRENCY"
            )
            awarded_currency = currency_elem[0] if currency_elem else None

        # Extract contractors
        contractors = _extract_contractors(award_elem)

        # Get title from contract info (reuse from parent)
        title_parts = root.xpath(".//BIB_DOC_S//TI_DOC/P/text()")
        title = title_parts[0] if title_parts else ""

        awards.append(
            AwardModel(
                award_title=title,
                conclusion_date=None,
                contract_number=contract_number or None,
                tenders_received=None,
                tenders_received_sme=None,
                tenders_received_other_eu=None,
                tenders_received_non_eu=None,
                tenders_received_electronic=None,
                awarded_value=awarded_value,
                awarded_value_currency=awarded_currency,
                subcontracted_value=None,
                subcontracted_value_currency=None,
                subcontracting_description=None,
                contractors=contractors,
            )
        )

    return awards


def _extract_contractors(award_elem: etree._Element) -> List[ContractorModel]:
    """Extract contractor information from award element."""
    contractors = []

    contractor_elems = award_elem.xpath(".//ECONOMIC_OPERATOR_NAME_ADDRESS")
    for contractor_elem in contractor_elems:
        contact_data_list = contractor_elem.xpath(
            ".//CONTACT_DATA_WITHOUT_RESPONSIBLE_NAME"
        )
        if not contact_data_list:
            continue

        contact_data = contact_data_list[0]
        org_name = xpath_text(contact_data, ".//ORGANISATION")
        if not org_name:
            continue

        address = xpath_text(contact_data, ".//ADDRESS")
        town = xpath_text(contact_data, ".//TOWN")
        postal_code = xpath_text(contact_data, ".//POSTAL_CODE")
        country = contact_data.xpath(".//COUNTRY/@VALUE")
        country_code = country[0] if country else None
        email = xpath_text(contact_data, ".//E_MAIL")
        phone = xpath_text(contact_data, ".//PHONE")
        fax = xpath_text(contact_data, ".//FAX")

        contractors.append(
            ContractorModel(
                official_name=org_name,
                address=address or None,
                town=town or None,
                postal_code=postal_code or None,
                country_code=country_code,
                nuts_code=None,
                phone=phone or None,
                email=email or None,
                fax=fax or None,
                url=None,
                is_sme=False,
            )
        )

    return contractors
