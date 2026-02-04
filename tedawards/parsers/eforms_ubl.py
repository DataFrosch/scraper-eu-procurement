"""
eForms UBL ContractAwardNotice parser for EU eForms standard (2025+).

Date formats in eForms UBL:
- IssueDate, PublicationDate: YYYY-MM-DD+HH:MM or YYYY-MM-DDZ
  Examples: "2025-01-02+01:00", "2024-12-30Z"
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
from .xml import first_text


def _parse_date_eforms(text: Optional[str]) -> Optional[date]:
    """
    Parse date from eForms format: YYYY-MM-DD+HH:MM or YYYY-MM-DDZ

    Examples: "2025-01-02+01:00", "2024-12-30-05:00", "2024-12-30Z"
    Extracts just the date portion, discarding the timezone.
    """
    if not text:
        return None

    stripped = text.strip()
    if not stripped:
        return None

    # Accept: YYYY-MM-DD+HH:MM, YYYY-MM-DD-HH:MM, or YYYY-MM-DDZ
    if not re.match(r"^\d{4}-\d{2}-\d{2}([+-]\d{2}:\d{2}|Z)$", stripped):
        return None

    # Extract just the date part (first 10 characters)
    date_part = stripped[:10]

    try:
        return date.fromisoformat(date_part)
    except ValueError:
        return None


logger = logging.getLogger(__name__)

# eForms namespaces
NAMESPACES = {
    "can": "urn:oasis:names:specification:ubl:schema:xsd:ContractAwardNotice-2",
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
    "efac": "http://data.europa.eu/p27/eforms-ubl-extension-aggregate-components/1",
    "efbc": "http://data.europa.eu/p27/eforms-ubl-extension-basic-components/1",
    "efext": "http://data.europa.eu/p27/eforms-ubl-extensions/1",
    "ext": "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2",
}


def parse_xml_file(xml_file: Path) -> Optional[List[TedAwardDataModel]]:
    """Parse eForms UBL XML file and return structured data."""
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
        logger.error(f"Error parsing eForms UBL file {xml_file}: {e}")
        raise


def _extract_document_info(
    root: etree._Element, xml_file: Path
) -> Optional[DocumentModel]:
    """Extract document metadata from eForms UBL."""
    # Extract document ID from filename
    doc_id = xml_file.stem
    # Normalize year separator: 000123_2024 -> 000123-2024
    doc_id = re.sub(r"_(\d{4})$", r"-\1", doc_id)

    # Extract publication date from various possible locations
    pub_date_elem = (
        root.xpath(".//efac:Publication/efbc:PublicationDate", namespaces=NAMESPACES)
        or root.xpath(".//cbc:IssueDate", namespaces=NAMESPACES)
        or root.xpath(".//efac:SettledContract/cbc:IssueDate", namespaces=NAMESPACES)
        or root.xpath(".//cac:ContractAwardNotice/cbc:IssueDate", namespaces=NAMESPACES)
    )

    if not pub_date_elem or not pub_date_elem[0].text:
        logger.error(f"No publication date found in eForms document {xml_file}")
        return None

    pub_date = _parse_date_eforms(pub_date_elem[0].text)
    if pub_date is None:
        logger.debug(f"Could not parse publication date in {xml_file}")
        return None

    # Extract sender country
    countries = root.xpath(
        ".//cac:Country/cbc:IdentificationCode/text()", namespaces=NAMESPACES
    )
    country = countries[0] if countries else ""

    # Create official journal reference
    year = pub_date.year
    day_of_year = pub_date.timetuple().tm_yday
    official_ref = f"{year}/S {day_of_year:03d}-{doc_id}"

    return DocumentModel(
        doc_id=doc_id,
        edition=f"{year}{day_of_year:03d}",
        version="eForms-UBL",
        official_journal_ref=official_ref,
        publication_date=pub_date,
        dispatch_date=pub_date,
        source_country=country,
    )


def _extract_contracting_body(root: etree._Element) -> Optional[ContractingBodyModel]:
    """Extract contracting body information from eForms UBL."""
    # Find the contracting party organization ID
    contracting_party_id_elem = root.xpath(
        ".//cac:ContractingParty/cac:Party/cac:PartyIdentification/cbc:ID",
        namespaces=NAMESPACES,
    )
    contracting_party_id = (
        contracting_party_id_elem[0].text
        if contracting_party_id_elem and contracting_party_id_elem[0].text
        else None
    )

    contracting_body = None

    if not contracting_party_id:
        # Fallback to first organization
        orgs = root.xpath(
            ".//efac:Organizations/efac:Organization", namespaces=NAMESPACES
        )
        if orgs:
            contracting_body = orgs[0].find(".//efac:Company", NAMESPACES)
    else:
        # Find the organization with matching ID
        orgs = root.xpath(
            ".//efac:Organizations/efac:Organization", namespaces=NAMESPACES
        )
        for org in orgs:
            company = org.find(".//efac:Company", NAMESPACES)
            if company is not None:
                org_id_elem = company.xpath(
                    ".//cac:PartyIdentification/cbc:ID", namespaces=NAMESPACES
                )
                org_id = (
                    org_id_elem[0].text if org_id_elem and org_id_elem[0].text else None
                )
                if org_id == contracting_party_id:
                    contracting_body = company
                    break

    if contracting_body is None:
        return None

    name_elem = contracting_body.xpath(
        ".//cac:PartyName/cbc:Name", namespaces=NAMESPACES
    )
    address_elem = contracting_body.xpath(
        ".//cac:PostalAddress/cbc:StreetName", namespaces=NAMESPACES
    )
    town_elem = contracting_body.xpath(
        ".//cac:PostalAddress/cbc:CityName", namespaces=NAMESPACES
    )
    postal_elem = contracting_body.xpath(
        ".//cac:PostalAddress/cbc:PostalZone", namespaces=NAMESPACES
    )
    country_elem = contracting_body.xpath(
        ".//cac:PostalAddress/cac:Country/cbc:IdentificationCode",
        namespaces=NAMESPACES,
    )
    phone_elem = contracting_body.xpath(
        ".//cac:Contact/cbc:Telephone", namespaces=NAMESPACES
    )
    email_elem = contracting_body.xpath(
        ".//cac:Contact/cbc:ElectronicMail", namespaces=NAMESPACES
    )
    url_elem = contracting_body.xpath(".//cbc:WebsiteURI", namespaces=NAMESPACES)

    return ContractingBodyModel(
        official_name=first_text(name_elem) or "",
        address=first_text(address_elem),
        town=first_text(town_elem),
        postal_code=first_text(postal_elem),
        country_code=first_text(country_elem),
        contact_point=None,
        phone=first_text(phone_elem),
        email=first_text(email_elem),
        url_general=first_text(url_elem),
        url_buyer=None,
        authority_type_code=None,
        main_activity_code=None,
    )


def _extract_contract_info(root: etree._Element) -> Optional[ContractModel]:
    """Extract contract information from eForms UBL."""
    title_elem = root.xpath(".//efac:SettledContract/cbc:Title", namespaces=NAMESPACES)
    title = first_text(title_elem) or ""

    cpv_elem = root.xpath(
        ".//cac:ProcurementProject/cac:MainCommodityClassification/cbc:ItemClassificationCode",
        namespaces=NAMESPACES,
    )
    nature_elem = root.xpath(
        ".//cac:ProcurementProject/cbc:ProcurementTypeCode", namespaces=NAMESPACES
    )
    proc_elem = root.xpath(
        ".//cac:TenderingProcess/cbc:ProcedureCode", namespaces=NAMESPACES
    )

    return ContractModel(
        title=title,
        short_description=title,
        main_cpv_code=first_text(cpv_elem),
        contract_nature_code=first_text(nature_elem),
        procedure_type_code=first_text(proc_elem),
    )


def _extract_awards(root: etree._Element) -> List[AwardModel]:
    """Extract award information from eForms UBL."""
    awards = []

    lot_results = root.xpath(".//efac:LotResult", namespaces=NAMESPACES)

    for lot_result in lot_results:
        # Get tender information
        tender_amount = root.xpath(
            ".//efac:LotTender/cac:LegalMonetaryTotal/cbc:PayableAmount",
            namespaces=NAMESPACES,
        )
        awarded_value = None
        awarded_currency = None
        if tender_amount and tender_amount[0].text:
            try:
                awarded_value = float(tender_amount[0].text)
            except (ValueError, TypeError) as e:
                logger.error(
                    f"Invalid awarded value: {tender_amount[0].text}. Error: {e}"
                )
                raise
            awarded_currency = tender_amount[0].get("currencyID")

        contractors = _extract_contractors(root)

        award_title_elem = root.xpath(
            ".//efac:SettledContract/cbc:Title", namespaces=NAMESPACES
        )
        contract_num_elem = root.xpath(
            ".//efac:SettledContract/efac:ContractReference/cbc:ID",
            namespaces=NAMESPACES,
        )

        awards.append(
            AwardModel(
                award_title=first_text(award_title_elem),
                contract_number=first_text(contract_num_elem),
                awarded_value=awarded_value,
                awarded_value_currency=awarded_currency,
                contractors=contractors,
            )
        )

    return awards


def _extract_contractors(root: etree._Element) -> List[ContractorModel]:
    """Extract contractor information from eForms UBL."""
    contractors = []

    # Find winning tenderer organization IDs
    winning_org_ids = set()
    tenderer_parties = root.xpath(".//efac:TenderingParty", namespaces=NAMESPACES)
    for party in tenderer_parties:
        tenderer_ids = party.xpath(
            ".//efac:Tenderer/cbc:ID/text()", namespaces=NAMESPACES
        )
        winning_org_ids.update(tenderer_ids)

    # Find contractor organizations by matching IDs
    orgs = root.xpath(".//efac:Organizations/efac:Organization", namespaces=NAMESPACES)

    for org in orgs:
        company = org.find(".//efac:Company", NAMESPACES)
        if company is not None:
            org_id_elem = company.xpath(
                ".//cac:PartyIdentification/cbc:ID", namespaces=NAMESPACES
            )
            org_id = (
                org_id_elem[0].text if org_id_elem and org_id_elem[0].text else None
            )

            if org_id in winning_org_ids:
                name_elem = company.xpath(
                    ".//cac:PartyName/cbc:Name", namespaces=NAMESPACES
                )
                official_name = first_text(name_elem)

                if official_name:
                    address_elem = company.xpath(
                        ".//cac:PostalAddress/cbc:StreetName", namespaces=NAMESPACES
                    )
                    town_elem = company.xpath(
                        ".//cac:PostalAddress/cbc:CityName", namespaces=NAMESPACES
                    )
                    postal_elem = company.xpath(
                        ".//cac:PostalAddress/cbc:PostalZone", namespaces=NAMESPACES
                    )
                    country_elem = company.xpath(
                        ".//cac:PostalAddress/cac:Country/cbc:IdentificationCode",
                        namespaces=NAMESPACES,
                    )

                    contractors.append(
                        ContractorModel(
                            official_name=official_name,
                            address=first_text(address_elem),
                            town=first_text(town_elem),
                            postal_code=first_text(postal_elem),
                            country_code=first_text(country_elem),
                        )
                    )

    return contractors
