"""
Tests for eForms UBL ContractAwardNotice format parser (2025+).

The eForms UBL format is the new EU standard for TED notices starting in 2025.
These tests validate:
1. Document parsing (parse_xml_file)
2. Data extraction (document, contracting body, contract, awards, contractors)
3. Data validation using Pydantic models
"""

import pytest
from pathlib import Path

from awards.portals.ted import eforms_ubl
from awards.schema import (
    AwardDataModel,
    DocumentModel,
    ContractingBodyModel,
    ContractModel,
    AwardModel,
    ContractorModel,
)


FIXTURES_DIR = Path(__file__).parent / "fixtures"

# List of eForms UBL fixtures (2025+)
EFORMS_UBL_FIXTURES = [
    "eforms_ubl_2025.xml",
    "eforms_ubl_2025_alt.xml",
]


class TestEFormsUBLParser:
    """Tests for eForms UBL ContractAwardNotice format parser."""

    @pytest.mark.parametrize("fixture_name", EFORMS_UBL_FIXTURES)
    def test_parse_eforms_ubl_document(self, fixture_name):
        """Test parsing eForms UBL format document."""
        fixture_file = FIXTURES_DIR / fixture_name
        result = eforms_ubl.parse_xml_file(fixture_file)

        # Validate result structure
        assert result is not None, f"Parser should return result for {fixture_name}"
        assert isinstance(result, list)
        assert len(result) > 0, f"Should extract at least one award from {fixture_name}"

        # Validate award data
        award_data = result[0]
        assert isinstance(award_data, AwardDataModel)

        # Validate document
        document = award_data.document
        assert isinstance(document, DocumentModel)
        assert document.doc_id, f"Document ID should be present in {fixture_name}"
        assert "2025" in document.doc_id, (
            f"Document ID should contain 2025 in {fixture_name}"
        )
        assert document.publication_date is not None, (
            f"Publication date should be present in {fixture_name}"
        )
        assert document.version == "eForms-UBL", (
            f"Version should be eForms-UBL in {fixture_name}"
        )

        # Validate contracting body
        contracting_body = award_data.contracting_body
        assert isinstance(contracting_body, ContractingBodyModel)
        assert contracting_body.official_name, (
            f"Contracting body name should be present in {fixture_name}"
        )
        assert contracting_body.country_code, (
            f"Country code should be present in {fixture_name}"
        )

        # Validate contract
        contract = award_data.contract
        assert isinstance(contract, ContractModel)
        assert contract.title, f"Contract title should be present in {fixture_name}"

        # Validate awards
        assert len(award_data.awards) > 0, (
            f"Should have at least one award in {fixture_name}"
        )
        award = award_data.awards[0]
        assert isinstance(award, AwardModel)

        # Validate contractors if present
        if award.contractors:
            for contractor in award.contractors:
                assert isinstance(contractor, ContractorModel)
                assert contractor.official_name, (
                    f"Contractor name should be present in {fixture_name}"
                )

    def test_parse_eforms_procedure_type(self):
        """Test procedure_type extraction for eForms."""
        fixture_file = FIXTURES_DIR / "eforms_ubl_2025.xml"
        result = eforms_ubl.parse_xml_file(fixture_file)
        assert result[0].contract.procedure_type.code == "open"
        assert result[0].contract.procedure_type.description == "Open procedure"

    def test_parse_eforms_cpv_codes_main_only(self):
        """Test CPV extraction for eForms with main code only (no additional)."""
        fixture_file = FIXTURES_DIR / "eforms_ubl_2025.xml"
        result = eforms_ubl.parse_xml_file(fixture_file)
        contract = result[0].contract

        assert contract.main_cpv_code == "33195000"
        assert len(contract.cpv_codes) == 1
        assert contract.cpv_codes[0].code == "33195000"
        assert contract.cpv_codes[0].description is None

    def test_parse_eforms_cpv_codes_with_additional(self):
        """Test CPV extraction for eForms with main + additional codes."""
        fixture_file = FIXTURES_DIR / "eforms_ubl_2025_alt.xml"
        result = eforms_ubl.parse_xml_file(fixture_file)
        contract = result[0].contract

        assert contract.main_cpv_code == "31520000"
        assert len(contract.cpv_codes) == 5
        assert contract.cpv_codes[0].code == "31520000"
        additional_codes = {c.code for c in contract.cpv_codes[1:]}
        assert additional_codes == {"45316110", "45311200", "45311100", "71355200"}

    def test_parse_eforms_tenders_received(self):
        """Test tenders_received extraction from ReceivedSubmissionsStatistics."""
        fixture_file = FIXTURES_DIR / "eforms_ubl_2025.xml"
        result = eforms_ubl.parse_xml_file(fixture_file)
        award = result[0].awards[0]
        assert award.tenders_received == 1

    def test_parse_eforms_lot_number(self):
        """Test lot_number extraction from LotResult/TenderLot."""
        fixture_file = FIXTURES_DIR / "eforms_ubl_2025.xml"
        result = eforms_ubl.parse_xml_file(fixture_file)
        award = result[0].awards[0]
        assert award.lot_number == "LOT-0000"

    def test_parse_eforms_lot_number_alt(self):
        """Test lot_number extraction from alt fixture."""
        fixture_file = FIXTURES_DIR / "eforms_ubl_2025_alt.xml"
        result = eforms_ubl.parse_xml_file(fixture_file)
        award = result[0].awards[0]
        assert award.lot_number == "LOT-0001"

    def test_parse_eforms_lot_scoped_value(self):
        """Test that awarded value is scoped to the correct lot tender."""
        fixture_file = FIXTURES_DIR / "eforms_ubl_2025.xml"
        result = eforms_ubl.parse_xml_file(fixture_file)
        award = result[0].awards[0]
        assert award.awarded_value == 23185.00
        assert award.awarded_value_currency == "EUR"

    def test_parse_eforms_lot_scoped_contractors(self):
        """Test that contractors are scoped to the correct lot via TenderingParty."""
        fixture_file = FIXTURES_DIR / "eforms_ubl_2025.xml"
        result = eforms_ubl.parse_xml_file(fixture_file)
        award = result[0].awards[0]
        assert len(award.contractors) == 1
        assert award.contractors[0].official_name == "Medivar OÜ"

    def test_parse_eforms_lot_scoped_title(self):
        """Test that award title is scoped from the correct SettledContract."""
        fixture_file = FIXTURES_DIR / "eforms_ubl_2025.xml"
        result = eforms_ubl.parse_xml_file(fixture_file)
        award = result[0].awards[0]
        assert award.award_title == "Hankeleping"
        assert award.contract_number == "HM 2024-63"

    def test_parse_eforms_framework_agreement(self):
        """Test framework_agreement extraction (none = False)."""
        fixture_file = FIXTURES_DIR / "eforms_ubl_2025.xml"
        result = eforms_ubl.parse_xml_file(fixture_file)
        assert result[0].contract.framework_agreement is False

    def test_parse_eforms_eu_funded(self):
        """Test eu_funded extraction (eu-funds = True)."""
        fixture_file = FIXTURES_DIR / "eforms_ubl_2025.xml"
        result = eforms_ubl.parse_xml_file(fixture_file)
        assert result[0].contract.eu_funded is True

    def test_parse_eforms_eu_not_funded(self):
        """Test eu_funded extraction (no-eu-funds = False)."""
        fixture_file = FIXTURES_DIR / "eforms_ubl_2025_alt.xml"
        result = eforms_ubl.parse_xml_file(fixture_file)
        assert result[0].contract.eu_funded is False

    def test_parse_eforms_estimated_value(self):
        """Test estimated_value extraction from ProcurementProjectLot."""
        fixture_file = FIXTURES_DIR / "eforms_ubl_2025_alt.xml"
        result = eforms_ubl.parse_xml_file(fixture_file)
        from decimal import Decimal

        assert result[0].contract.estimated_value == Decimal("1158540")
        assert result[0].contract.estimated_value_currency == "PLN"

    def test_parse_eforms_contract_period(self):
        """Test contract_start_date and contract_end_date from PlannedPeriod."""
        from datetime import date

        fixture_file = FIXTURES_DIR / "eforms_ubl_2025_alt.xml"
        result = eforms_ubl.parse_xml_file(fixture_file)
        award = result[0].awards[0]
        assert award.contract_start_date == date(2024, 11, 27)
        assert award.contract_end_date == date(2025, 4, 16)

    def test_parse_eforms_contracting_body_identifier(self):
        """Test organization identifier extraction for contracting body."""
        fixture_file = FIXTURES_DIR / "eforms_ubl_2025.xml"
        result = eforms_ubl.parse_xml_file(fixture_file)
        cb = result[0].contracting_body
        assert len(cb.identifiers) == 1
        assert cb.identifiers[0].scheme == "ORG"
        assert cb.identifiers[0].identifier == "90004585"

    def test_parse_eforms_contractor_identifier(self):
        """Test organization identifier extraction for contractor."""
        fixture_file = FIXTURES_DIR / "eforms_ubl_2025.xml"
        result = eforms_ubl.parse_xml_file(fixture_file)
        contractor = result[0].awards[0].contractors[0]
        assert len(contractor.identifiers) == 1
        assert contractor.identifiers[0].scheme == "ORG"
        assert contractor.identifiers[0].identifier == "12339040"

    def test_parse_eforms_award_date_skips_placeholder(self):
        """Test that placeholder award date 2000-01-01 is skipped."""
        fixture_file = FIXTURES_DIR / "eforms_ubl_2025.xml"
        result = eforms_ubl.parse_xml_file(fixture_file)
        award = result[0].awards[0]
        assert award.award_date is None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
