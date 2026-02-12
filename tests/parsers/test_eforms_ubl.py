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

from tedawards.parsers import eforms_ubl
from tedawards.schema import (
    TedAwardDataModel,
    DocumentModel,
    ContractingBodyModel,
    ContractModel,
    AwardModel,
    ContractorModel,
)


FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"

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
        assert isinstance(award_data, TedAwardDataModel)

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
        """Test procedure_type extraction for eForms (code only, no description)."""
        fixture_file = FIXTURES_DIR / "eforms_ubl_2025.xml"
        result = eforms_ubl.parse_xml_file(fixture_file)
        assert result[0].contract.procedure_type.code == "open"
        assert result[0].contract.procedure_type.description is None

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


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
