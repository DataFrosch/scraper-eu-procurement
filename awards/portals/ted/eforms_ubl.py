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

from ...schema import (
    AwardDataModel,
    DocumentModel,
    OrganizationModel,
    ContractModel,
    CpvCodeEntry,
    AwardModel,
    IdentifierEntry,
)
from .ted_v2 import _normalize_contract_nature_code, _normalize_procedure_type
from ...parsers.xml import first_attr, first_text


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


def _parse_optional_int(text: Optional[str], field_name: str) -> Optional[int]:
    """Parse an optional integer field from eForms XML.

    Accepts plain integers ("3") and whole-number floats ("3.0") since
    eForms UBL NumericType is decimal-based. Logs a warning for anything else.
    """
    if text is None:
        return None
    stripped = text.strip()
    if not stripped:
        return None
    if re.match(r"^\d+$", stripped):
        return int(stripped)
    if re.match(r"^\d+\.0+$", stripped):
        return int(stripped.split(".")[0])
    logger.warning(
        "Invalid integer value for %s: %r",
        field_name,
        text,
    )
    return None


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


def parse_xml_file(xml_file: Path) -> Optional[List[AwardDataModel]]:
    """Parse eForms UBL XML file and return structured data."""
    try:
        tree = etree.parse(xml_file)
        root = tree.getroot()

        document = _extract_document_info(root, xml_file)
        if not document:
            return None

        buyer, contact_fields = _extract_buyer(root)
        if not buyer:
            logger.debug(f"No contracting body found in {xml_file.name}")
            return None

        # Add contact fields to document
        document = document.model_copy(update=contact_fields)

        contract = _extract_contract_info(root)
        if not contract:
            logger.debug(f"No contract info found in {xml_file.name}")
            return None

        awards = _extract_awards(root)
        if not awards:
            logger.debug(f"No awards found in {xml_file.name}")
            return None

        return [
            AwardDataModel(
                document=document,
                buyer=buyer,
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


def _extract_buyer(
    root: etree._Element,
) -> tuple[Optional[OrganizationModel], dict]:
    """Extract buyer organization from eForms UBL.

    Returns (organization, contact_fields_dict).
    Contact fields belong on the document, not the organization.
    """
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

    company_elem = None

    if not contracting_party_id:
        # Fallback to first organization
        orgs = root.xpath(
            ".//efac:Organizations/efac:Organization", namespaces=NAMESPACES
        )
        if orgs:
            company_elem = orgs[0].find(".//efac:Company", NAMESPACES)
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
                    company_elem = company
                    break

    if company_elem is None:
        return None, {}

    name_elem = company_elem.xpath(".//cac:PartyName/cbc:Name", namespaces=NAMESPACES)
    address_elem = company_elem.xpath(
        ".//cac:PostalAddress/cbc:StreetName", namespaces=NAMESPACES
    )
    town_elem = company_elem.xpath(
        ".//cac:PostalAddress/cbc:CityName", namespaces=NAMESPACES
    )
    postal_elem = company_elem.xpath(
        ".//cac:PostalAddress/cbc:PostalZone", namespaces=NAMESPACES
    )
    country_elem = company_elem.xpath(
        ".//cac:PostalAddress/cac:Country/cbc:IdentificationCode",
        namespaces=NAMESPACES,
    )
    phone_elem = company_elem.xpath(
        ".//cac:Contact/cbc:Telephone", namespaces=NAMESPACES
    )
    email_elem = company_elem.xpath(
        ".//cac:Contact/cbc:ElectronicMail", namespaces=NAMESPACES
    )
    url_elem = company_elem.xpath(".//cbc:WebsiteURI", namespaces=NAMESPACES)
    nuts_elem = company_elem.xpath(
        ".//cac:PostalAddress/cbc:CountrySubentityCode", namespaces=NAMESPACES
    )

    contact_fields = {
        "phone": first_text(phone_elem),
        "email": first_text(email_elem),
        "url_general": first_text(url_elem),
    }

    # Extract organization identifier (BT-501)
    identifiers = []
    company_id_elem = company_elem.xpath(
        ".//cac:PartyLegalEntity/cbc:CompanyID", namespaces=NAMESPACES
    )
    company_id = first_text(company_id_elem)
    if company_id:
        scheme = first_attr(company_id_elem, "schemeName")
        scheme_id = first_attr(company_id_elem, "schemeID")
        if scheme_id:
            logger.warning(
                "CompanyID has schemeID=%r (not part of eForms SDK), value=%r",
                scheme_id,
                company_id,
            )
        identifiers.append(IdentifierEntry(scheme=scheme, identifier=company_id))

    org = OrganizationModel(
        official_name=first_text(name_elem) or "",
        address=first_text(address_elem),
        town=first_text(town_elem),
        postal_code=first_text(postal_elem),
        country_code=first_text(country_elem),
        nuts_code=first_text(nuts_elem),
        identifiers=identifiers,
    )

    return org, contact_fields


def _extract_contract_info(root: etree._Element) -> Optional[ContractModel]:
    """Extract contract information from eForms UBL."""
    title_elem = root.xpath(".//efac:SettledContract/cbc:Title", namespaces=NAMESPACES)
    title = first_text(title_elem) or ""

    # Main CPV from top-level ProcurementProject (direct child, not lot-level to avoid duplicates)
    cpv_main_elems = root.xpath(
        "./cac:ProcurementProject/cac:MainCommodityClassification/cbc:ItemClassificationCode",
        namespaces=NAMESPACES,
    )

    # Additional CPVs from top-level ProcurementProject (direct child)
    cpv_additional_elems = root.xpath(
        "./cac:ProcurementProject/cac:AdditionalCommodityClassification/cbc:ItemClassificationCode",
        namespaces=NAMESPACES,
    )

    nature_elem = root.xpath(
        ".//cac:ProcurementProject/cbc:ProcurementTypeCode", namespaces=NAMESPACES
    )
    proc_elem = root.xpath(
        ".//cac:TenderingProcess/cbc:ProcedureCode", namespaces=NAMESPACES
    )

    # Performance location NUTS - try lot-level first, then main project level
    nuts_elem = root.xpath(
        ".//cac:ProcurementProjectLot//cac:RealizedLocation//cbc:CountrySubentityCode",
        namespaces=NAMESPACES,
    ) or root.xpath(
        ".//cac:ProcurementProject/cac:RealizedLocation//cbc:CountrySubentityCode",
        namespaces=NAMESPACES,
    )

    # Build CPV codes list (no descriptions available in eForms)
    cpv_codes: list[CpvCodeEntry] = []

    main_code = first_text(cpv_main_elems)
    if main_code:
        cpv_codes.append(CpvCodeEntry(code=main_code))

    for additional_elem in cpv_additional_elems:
        additional_code = additional_elem.text
        if additional_code and additional_code.strip():
            cpv_codes.append(CpvCodeEntry(code=additional_code.strip()))

    proc_code = first_text(proc_elem)
    procedure_type, accelerated = _normalize_procedure_type(proc_code, None)

    # BT-106: Procedure Accelerated — separate boolean in eForms
    if not accelerated:
        accel_elems = root.xpath(
            ".//cac:TenderingProcess/cac:ProcessJustification"
            "/cbc:ProcessReasonCode[@listName='accelerated-procedure']",
            namespaces=NAMESPACES,
        )
        if accel_elems and first_text(accel_elems) == "true":
            accelerated = True

    # BT-27: Estimated value from lot-level ProcurementProject
    estimated_value = None
    estimated_value_currency = None
    est_val_elems = root.xpath(
        ".//cac:ProcurementProjectLot/cac:ProcurementProject"
        "/cac:RequestedTenderTotal/cbc:EstimatedOverallContractAmount",
        namespaces=NAMESPACES,
    )
    if est_val_elems and est_val_elems[0].text:
        try:
            from decimal import Decimal

            estimated_value = Decimal(est_val_elems[0].text.strip())
            estimated_value_currency = est_val_elems[0].get("currencyID")
        except Exception:
            pass

    # BT-765: Framework agreement
    framework_elems = root.xpath(
        ".//cac:ProcurementProjectLot//cbc:ContractingSystemTypeCode"
        "[@listName='framework-agreement']",
        namespaces=NAMESPACES,
    )
    framework_agreement = False
    if framework_elems:
        fw_value = first_text(framework_elems)
        if fw_value and fw_value != "none":
            framework_agreement = True

    # BT-60: EU funded
    eu_funded_elems = root.xpath(
        ".//cac:ProcurementProjectLot//cbc:FundingProgramCode[@listName='eu-funded']",
        namespaces=NAMESPACES,
    )
    eu_funded = False
    if eu_funded_elems:
        eu_value = first_text(eu_funded_elems)
        if eu_value == "eu-funds":
            eu_funded = True

    return ContractModel(
        title=title,
        short_description=title,
        main_cpv_code=main_code,
        cpv_codes=cpv_codes,
        nuts_code=first_text(nuts_elem),
        contract_nature_code=_normalize_contract_nature_code(first_text(nature_elem)),
        procedure_type=procedure_type,
        accelerated=accelerated,
        estimated_value=estimated_value,
        estimated_value_currency=estimated_value_currency,
        framework_agreement=framework_agreement,
        eu_funded=eu_funded,
    )


def _extract_awards(root: etree._Element) -> List[AwardModel]:
    """Extract award information from eForms UBL using reference-based lookups.

    eForms uses ID cross-references between sibling elements under NoticeResult:
    - LotResult references a LotTender (tender ID) and SettledContract (contract ID)
    - LotTender references a TenderingParty (party ID) and contains the awarded value
    - SettledContract contains title and contract number
    - TenderingParty references Tenderer org IDs
    """
    awards = []

    # Build organization lookup: org_id -> Company element
    org_lookup: dict[str, etree._Element] = {}
    for org in root.xpath(
        ".//efac:Organizations/efac:Organization", namespaces=NAMESPACES
    ):
        company = org.find(".//efac:Company", NAMESPACES)
        if company is not None:
            org_id_elem = company.xpath(
                ".//cac:PartyIdentification/cbc:ID", namespaces=NAMESPACES
            )
            org_id = (
                org_id_elem[0].text if org_id_elem and org_id_elem[0].text else None
            )
            if org_id:
                org_lookup[org_id] = company

    # Build lookup dicts from NoticeResult sibling elements
    lot_tenders: dict[str, etree._Element] = {}
    for lt in root.xpath(".//efac:NoticeResult/efac:LotTender", namespaces=NAMESPACES):
        tender_id_elem = lt.xpath("cbc:ID", namespaces=NAMESPACES)
        if tender_id_elem and tender_id_elem[0].text:
            lot_tenders[tender_id_elem[0].text] = lt

    settled_contracts: dict[str, etree._Element] = {}
    for sc in root.xpath(
        ".//efac:NoticeResult/efac:SettledContract", namespaces=NAMESPACES
    ):
        contract_id_elem = sc.xpath("cbc:ID", namespaces=NAMESPACES)
        if contract_id_elem and contract_id_elem[0].text:
            settled_contracts[contract_id_elem[0].text] = sc

    tendering_parties: dict[str, etree._Element] = {}
    for tp in root.xpath(
        ".//efac:NoticeResult/efac:TenderingParty", namespaces=NAMESPACES
    ):
        party_id_elem = tp.xpath("cbc:ID", namespaces=NAMESPACES)
        if party_id_elem and party_id_elem[0].text:
            tendering_parties[party_id_elem[0].text] = tp

    # Build lot PlannedPeriod lookup: lot_id -> (start_date, end_date)
    lot_periods: dict[str, tuple[Optional[date], Optional[date]]] = {}
    for lot_elem in root.xpath(".//cac:ProcurementProjectLot", namespaces=NAMESPACES):
        lot_id_elem = lot_elem.xpath("cbc:ID", namespaces=NAMESPACES)
        if lot_id_elem and lot_id_elem[0].text:
            lot_id = lot_id_elem[0].text
            start_elems = lot_elem.xpath(
                ".//cac:PlannedPeriod/cbc:StartDate", namespaces=NAMESPACES
            )
            end_elems = lot_elem.xpath(
                ".//cac:PlannedPeriod/cbc:EndDate", namespaces=NAMESPACES
            )
            start_date = (
                _parse_date_eforms(start_elems[0].text) if start_elems else None
            )
            end_date = _parse_date_eforms(end_elems[0].text) if end_elems else None
            lot_periods[lot_id] = (start_date, end_date)

    # Extract award_date from TenderResult (document-level)
    award_date = None
    award_date_elems = root.xpath(
        ".//cac:TenderResult/cbc:AwardDate", namespaces=NAMESPACES
    )
    if award_date_elems:
        parsed = _parse_date_eforms(award_date_elems[0].text)
        # Skip placeholder values like 2000-01-01
        if parsed and parsed.year >= 2005:
            award_date = parsed

    # Process each LotResult
    lot_results = root.xpath(".//efac:LotResult", namespaces=NAMESPACES)
    for lot_result in lot_results:
        # Get lot number
        lot_ref_elems = lot_result.xpath("efac:TenderLot/cbc:ID", namespaces=NAMESPACES)
        lot_number = first_text(lot_ref_elems)

        # Get tender ID -> look up LotTender -> extract value + TenderingParty ID
        tender_ref_elems = lot_result.xpath(
            "efac:LotTender/cbc:ID", namespaces=NAMESPACES
        )
        tender_id = first_text(tender_ref_elems)

        awarded_value = None
        awarded_currency = None
        party_id = None
        if tender_id and tender_id in lot_tenders:
            lot_tender = lot_tenders[tender_id]
            amount_elems = lot_tender.xpath(
                "cac:LegalMonetaryTotal/cbc:PayableAmount", namespaces=NAMESPACES
            )
            if amount_elems and amount_elems[0].text:
                try:
                    awarded_value = float(amount_elems[0].text)
                except (ValueError, TypeError) as e:
                    logger.error(
                        f"Invalid awarded value: {amount_elems[0].text}. Error: {e}"
                    )
                    raise
                awarded_currency = amount_elems[0].get("currencyID")

            # Get TenderingParty ID from LotTender
            party_ref_elems = lot_tender.xpath(
                "efac:TenderingParty/cbc:ID", namespaces=NAMESPACES
            )
            party_id = first_text(party_ref_elems)

        # Get contract ID -> look up SettledContract -> extract title + contract number
        contract_ref_elems = lot_result.xpath(
            "efac:SettledContract/cbc:ID", namespaces=NAMESPACES
        )
        contract_id = first_text(contract_ref_elems)

        award_title = None
        contract_number = None
        if contract_id and contract_id in settled_contracts:
            sc = settled_contracts[contract_id]
            title_elems = sc.xpath("cbc:Title", namespaces=NAMESPACES)
            award_title = first_text(title_elems)
            ref_elems = sc.xpath("efac:ContractReference/cbc:ID", namespaces=NAMESPACES)
            contract_number = first_text(ref_elems)

        # Extract tenders_received from ReceivedSubmissionsStatistics
        stats = lot_result.xpath(
            "efac:ReceivedSubmissionsStatistics"
            "[efbc:StatisticsCode='tenders']"
            "/efbc:StatisticsNumeric/text()",
            namespaces=NAMESPACES,
        )
        tenders_received = (
            _parse_optional_int(stats[0], "tenders_received") if stats else None
        )

        # Follow TenderingParty -> Tenderer org IDs -> resolve to contractors
        contractors = []
        if party_id and party_id in tendering_parties:
            tp = tendering_parties[party_id]
            tenderer_org_ids = tp.xpath(
                "efac:Tenderer/cbc:ID/text()", namespaces=NAMESPACES
            )
            for org_id in tenderer_org_ids:
                if org_id in org_lookup:
                    contractor = _company_to_contractor(org_lookup[org_id])
                    if contractor:
                        contractors.append(contractor)

        # Get contract period from lot PlannedPeriod
        contract_start_date = None
        contract_end_date = None
        if lot_number and lot_number in lot_periods:
            contract_start_date, contract_end_date = lot_periods[lot_number]

        awards.append(
            AwardModel(
                award_title=award_title,
                contract_number=contract_number,
                awarded_value=awarded_value,
                awarded_value_currency=awarded_currency,
                tenders_received=tenders_received,
                award_date=award_date,
                lot_number=lot_number,
                contract_start_date=contract_start_date,
                contract_end_date=contract_end_date,
                contractors=contractors,
            )
        )

    return awards


def _company_to_contractor(
    company_elem: etree._Element,
) -> Optional[OrganizationModel]:
    """Convert an eForms Company element to an OrganizationModel."""
    name_elem = company_elem.xpath(".//cac:PartyName/cbc:Name", namespaces=NAMESPACES)
    official_name = first_text(name_elem)
    if not official_name:
        return None

    address_elem = company_elem.xpath(
        ".//cac:PostalAddress/cbc:StreetName", namespaces=NAMESPACES
    )
    town_elem = company_elem.xpath(
        ".//cac:PostalAddress/cbc:CityName", namespaces=NAMESPACES
    )
    postal_elem = company_elem.xpath(
        ".//cac:PostalAddress/cbc:PostalZone", namespaces=NAMESPACES
    )
    country_elem = company_elem.xpath(
        ".//cac:PostalAddress/cac:Country/cbc:IdentificationCode",
        namespaces=NAMESPACES,
    )
    nuts_elem = company_elem.xpath(
        ".//cac:PostalAddress/cbc:CountrySubentityCode",
        namespaces=NAMESPACES,
    )

    # Extract organization identifier (BT-501)
    identifiers = []
    company_id_elem = company_elem.xpath(
        ".//cac:PartyLegalEntity/cbc:CompanyID", namespaces=NAMESPACES
    )
    company_id = first_text(company_id_elem)
    if company_id:
        scheme = first_attr(company_id_elem, "schemeName")
        scheme_id = first_attr(company_id_elem, "schemeID")
        if scheme_id:
            logger.warning(
                "CompanyID has schemeID=%r (not part of eForms SDK), value=%r",
                scheme_id,
                company_id,
            )
        identifiers.append(IdentifierEntry(scheme=scheme, identifier=company_id))

    return OrganizationModel(
        official_name=official_name,
        address=first_text(address_elem),
        town=first_text(town_elem),
        postal_code=first_text(postal_elem),
        country_code=first_text(country_elem),
        nuts_code=first_text(nuts_elem),
        identifiers=identifiers,
    )
