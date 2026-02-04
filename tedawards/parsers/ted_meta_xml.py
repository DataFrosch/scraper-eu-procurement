"""
TED META XML format parser for legacy formats (2007-2013).
Handles the META XML format contained in ZIP archives.
"""

import logging
import re
import zipfile
from pathlib import Path
from typing import List, Optional

from lxml import etree

from .xml import xpath_text, parse_date_yyyymmdd
from ..schema import (
    TedAwardDataModel,
    DocumentModel,
    ContractingBodyModel,
    ContractModel,
    AwardModel,
    ContractorModel,
)

logger = logging.getLogger(__name__)

FORMAT_NAME = "TED META XML"


def can_parse(file_path: Path) -> bool:
    """Check if this file uses TED META XML format."""
    if not _is_ted_text_format(file_path):
        return False

    # Check if the wrapper filename contains _meta_org or _meta
    if "_meta_org." in file_path.name.lower() or "_meta" in file_path.name.lower():
        return True

    # Check contents for test fixtures with simplified names
    try:
        with zipfile.ZipFile(file_path, "r") as zf:
            names = zf.namelist()
            for name in names:
                if "META_ORG" in name.upper():
                    return True
    except (zipfile.BadZipFile, OSError):
        pass

    return False


def _is_ted_text_format(file_path: Path) -> bool:
    """Check if this file uses TED text format (ZIP containing text files)."""
    try:
        if not file_path.name.upper().endswith(".ZIP"):
            return False

        # Check for language-specific ZIP file pattern
        pattern = r"^[a-zA-Z]{2}_\d{8}_\d+_(utf8|meta|iso)_org"

        # First check the wrapper filename
        if re.match(pattern, file_path.name, re.IGNORECASE):
            return True

        # Check contents for test fixtures
        try:
            with zipfile.ZipFile(file_path, "r") as zf:
                names = zf.namelist()
                for name in names:
                    if re.match(pattern, name, re.IGNORECASE):
                        return True
        except (zipfile.BadZipFile, OSError):
            pass

        return False
    except Exception as e:
        logger.debug(f"Error checking if {file_path.name} is TED text format: {e}")
        return False


def get_format_name() -> str:
    """Return the format name for this parser."""
    return FORMAT_NAME


def parse_xml_file(file_path: Path) -> Optional[List[TedAwardDataModel]]:
    """Parse a TED META XML format ZIP file and extract award data.

    This format contains multiple documents in a ZIP archive.
    """
    try:
        return _parse_meta_xml_zip(file_path)
    except Exception as e:
        logger.error(f"Error parsing {file_path.name}: {e}")
        raise


def _parse_meta_xml_zip(zip_path: Path) -> Optional[List[TedAwardDataModel]]:
    """Parse META XML ZIP file and extract all award notices."""
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
        if not names:
            logger.warning(f"No files found in {zip_path}")
            return None

        # Read and parse XML content
        xml_content = zf.read(names[0]).decode("utf-8", errors="ignore")
        root = etree.fromstring(xml_content.encode("utf-8"))

        # Find all award documents
        award_records = []

        # Process CONTRACT_AWARD elements (English only)
        for doc in root.xpath('.//CONTRACT_AWARD[@category="orig"]'):
            if doc.get("lg", "").upper() == "EN":
                award_data = _convert_meta_xml_to_standard_format(doc)
                if award_data:
                    award_records.append(award_data)

        # Process OTH_NOT elements with award notices (English only)
        for doc in root.xpath('.//OTH_NOT[@category="orig"]'):
            natnotice = doc.xpath('.//natnotice[@code="7"]')
            if natnotice and doc.get("lg", "").upper() == "EN":
                award_data = _convert_meta_xml_to_standard_format(doc)
                if award_data:
                    award_records.append(award_data)

        if award_records:
            logger.debug(f"Found {len(award_records)} award records in {zip_path.name}")
            return award_records
        else:
            logger.debug(f"No award records found in {zip_path.name}")
            return None


def _convert_meta_xml_to_standard_format(
    doc_elem: etree._Element,
) -> Optional[TedAwardDataModel]:
    """Convert META XML document element to standardized format."""
    doc_parent = doc_elem.getparent()
    if doc_parent is None:
        logger.warning("No parent doc element found")
        return None

    doc_id = doc_parent.get("id", "")
    current_lang = doc_elem.get("lg", "")

    # Extract codified data
    codifdata_list = doc_elem.xpath(".//codifdata")
    if not codifdata_list:
        logger.warning(f"No codified data found in document {doc_id}")
        return None
    codifdata = codifdata_list[0]

    # Get document reference and metadata
    nodocojs = xpath_text(codifdata, "./nodocojs") or doc_id
    datedisp = xpath_text(codifdata, "./datedisp") or ""
    isocountry = xpath_text(codifdata, "./isocountry") or ""

    # Parse publication date from refojs
    pub_date = None
    datepub = ""
    refojs_list = doc_elem.xpath(".//refojs")
    if refojs_list:
        datepub = xpath_text(refojs_list[0], "./datepub") or ""
        if datepub and len(datepub) == 8:
            try:
                pub_date = parse_date_yyyymmdd(datepub)
            except ValueError:
                logger.warning(f"Invalid publication date format: {datepub}")

    # Parse dispatch date
    dispatch_date_obj = None
    if datedisp and len(datedisp) == 8:
        try:
            dispatch_date_obj = parse_date_yyyymmdd(datedisp)
        except ValueError:
            pass

    # Build universal document identifier
    full_doc_id = f"meta-{nodocojs}-{datepub}" if datepub else f"meta-{nodocojs}"

    # Extract title from tidoc
    title = ""
    tidoc = doc_elem.xpath(".//tidoc/p[1]/text()")
    if tidoc:
        title = tidoc[0].strip()

    # Extract contracting body info
    contracting_body_name = ""
    contracting_body_town = ""

    org_elem = doc_elem.xpath(".//organisation/text()")
    if org_elem:
        contracting_body_name = org_elem[0].strip()

    town_elem = doc_elem.xpath(".//town/text()")
    if town_elem:
        contracting_body_town = town_elem[0].strip()

    # Extract CPV code
    main_cpv_code = ""
    originalcpv = codifdata.xpath("./originalcpv/@code")
    if originalcpv:
        main_cpv_code = originalcpv[0]

    # Extract contract value
    contract_value = _parse_xml_contract_value(doc_elem)

    # Extract contractors
    contractors = _parse_xml_contractors(doc_elem)

    # Build award data using Pydantic models
    document = DocumentModel(
        doc_id=full_doc_id,
        edition="1",
        version="1",
        reception_id=nodocojs,
        deletion_date=None,
        official_journal_ref=f"{datepub}/{nodocojs}" if datepub else nodocojs,
        publication_date=pub_date,
        dispatch_date=dispatch_date_obj,
        source_country=isocountry or None,
    )

    contracting_body = ContractingBodyModel(
        official_name=contracting_body_name,
        address=None,
        town=contracting_body_town or None,
        postal_code=None,
        country_code=isocountry or None,
        nuts_code=None,
        contact_point=None,
        phone=None,
        email=None,
        fax=None,
        url_general=None,
        url_buyer=None,
        authority_type_code=None,
        main_activity_code=None,
    )

    contract = ContractModel(
        title=title,
        reference_number=nodocojs,
        short_description=None,
        main_cpv_code=main_cpv_code or None,
        contract_nature_code=None,
        total_value=contract_value,
        total_value_currency="EUR" if contract_value else None,
        procedure_type_code=None,
        award_criteria_code=None,
        performance_nuts_code=None,
    )

    award = AwardModel(
        award_title=title,
        conclusion_date=dispatch_date_obj,
        contract_number=nodocojs,
        tenders_received=None,
        tenders_received_sme=None,
        tenders_received_other_eu=None,
        tenders_received_non_eu=None,
        tenders_received_electronic=None,
        awarded_value=contract_value,
        awarded_value_currency="EUR" if contract_value else None,
        subcontracted_value=None,
        subcontracted_value_currency=None,
        subcontracting_description=None,
        contractors=contractors,
    )

    logger.debug(f"Converted XML document {doc_id} (language: {current_lang})")

    return TedAwardDataModel(
        document=document,
        contracting_body=contracting_body,
        contract=contract,
        awards=[award],
    )


def _parse_xml_contract_value(doc_elem: etree._Element) -> Optional[float]:
    """Extract contract value from XML contents."""
    # Look for EUR amounts in text content
    contents_text = ""
    for text_elem in doc_elem.xpath(".//contents//text()"):
        contents_text += text_elem + " "

    if contents_text:
        value_patterns = [
            r"EUR\s*([\d,.\s]+)",
            r"€\s*([\d,.\s]+)",
            r"([\d,.\s]+)\s*EUR",
            r"([\d,.\s]+)\s*€",
        ]

        for pattern in value_patterns:
            match = re.search(pattern, contents_text, re.IGNORECASE)
            if match:
                value_str = match.group(1).replace(",", "").replace(" ", "")
                try:
                    return float(value_str)
                except ValueError:
                    continue

    return None


def _parse_xml_contractors(doc_elem: etree._Element) -> List[ContractorModel]:
    """Extract contractor information from XML contents."""
    contractors = []

    org_elems = doc_elem.xpath(".//contents//organisation/text()")
    for org_name in org_elems:
        if org_name.strip():
            contractors.append(
                ContractorModel(
                    official_name=org_name.strip(),
                    address=None,
                    town=None,
                    postal_code=None,
                    country_code=None,
                    nuts_code=None,
                    phone=None,
                    email=None,
                    fax=None,
                    url=None,
                    is_sme=False,
                )
            )

    return contractors
