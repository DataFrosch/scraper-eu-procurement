"""
Tests for TED 2.0 XML format parser.

The unified TED 2.0 parser handles multiple format variants:
- R2.0.7 (2011-2013): XML with CONTRACT_AWARD forms, early structure
- R2.0.8 (2014-2015): XML with CONTRACT_AWARD forms, enhanced structure
- R2.0.9 (2014-2024): XML with F03_2014 forms, modern structure

These tests validate:
1. Document parsing (parse_xml_file)
2. Data extraction (document, contracting body, contract, awards, contractors)
3. Data validation using Pydantic models
"""

import pytest
from pathlib import Path
from datetime import date

from awards.portals.ted import ted_v2
from awards.schema import (
    AwardDataModel,
    DocumentModel,
    ContractingBodyModel,
    ContractModel,
    AwardModel,
    ContractorModel,
)


FIXTURES_DIR = Path(__file__).parent / "fixtures"

# List of TED 2.0 R2.0.7 fixtures (2011-2013)
TED_V2_R207_FIXTURES = [
    "ted_v2_r2_0_7_2011.xml",
]

# List of TED 2.0 R2.0.8 fixtures (2014-2015)
TED_V2_R208_FIXTURES = [
    "ted_v2_r2_0_8_2015.xml",
]

# List of TED 2.0 R2.0.9 fixtures (2014-2024)
TED_V2_R209_FIXTURES = [
    "ted_v2_r2_0_9_2024.xml",
]


class TestTedV2R207Parser:
    """Tests for TED 2.0 R2.0.7 format parser."""

    @pytest.mark.parametrize("fixture_name", TED_V2_R207_FIXTURES)
    def test_parse_r207_document(self, fixture_name):
        """Test parsing R2.0.7 format document."""
        fixture_file = FIXTURES_DIR / fixture_name
        result = ted_v2.parse_xml_file(fixture_file)

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
        assert document.publication_date is not None, (
            f"Publication date should be present in {fixture_name}"
        )
        assert document.version, f"Version should be present in {fixture_name}"
        assert "R2.0.7" in document.version or "R2.0.7/R2.0.8" in document.version

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

    def test_parse_r207_awarded_value_from_text_content(self):
        """Test that awarded_value is parsed from text content (European format)."""
        fixture_file = FIXTURES_DIR / "ted_v2_r2_0_7_2011.xml"
        result = ted_v2.parse_xml_file(fixture_file)

        # First award in fixture has VALUE_COST text "408 000,00"
        award = result[0].awards[0]
        assert award.awarded_value == 408000.00
        assert award.awarded_value_currency == "GBP"

    def test_parse_r207_procedure_type(self):
        """Test procedure_type extraction for R2.0.7."""
        fixture_file = FIXTURES_DIR / "ted_v2_r2_0_7_2011.xml"
        result = ted_v2.parse_xml_file(fixture_file)
        assert result[0].contract.procedure_type.code == "restricted"
        assert result[0].contract.procedure_type.description == "Restricted procedure"

    def test_parse_r207_contract_nature_normalized(self):
        """Test contract nature code is normalized from old '4' to 'services'."""
        fixture_file = FIXTURES_DIR / "ted_v2_r2_0_7_2011.xml"
        result = ted_v2.parse_xml_file(fixture_file)
        assert result[0].contract.contract_nature_code == "services"

    def test_parse_r207_authority_type_normalized(self):
        """Test authority type code is normalized from old '3' to 'ra'."""
        fixture_file = FIXTURES_DIR / "ted_v2_r2_0_7_2011.xml"
        result = ted_v2.parse_xml_file(fixture_file)
        cb = result[0].contracting_body
        assert cb.authority_type is not None
        assert cb.authority_type.code == "ra"
        assert cb.authority_type.description == "Regional authority"

    def test_parse_r207_cpv_codes(self):
        """Test CPV code extraction for R2.0.7: main + additional with descriptions."""
        fixture_file = FIXTURES_DIR / "ted_v2_r2_0_7_2011.xml"
        result = ted_v2.parse_xml_file(fixture_file)
        contract = result[0].contract

        assert contract.main_cpv_code == "85147000"
        assert len(contract.cpv_codes) == 2
        assert contract.cpv_codes[0].code == "85147000"
        assert contract.cpv_codes[0].description == "company health services"
        assert contract.cpv_codes[1].code == "85140000"
        assert contract.cpv_codes[1].description == "miscellaneous health services"


class TestTedV2R208Parser:
    """Tests for TED 2.0 R2.0.8 format parser."""

    @pytest.mark.parametrize("fixture_name", TED_V2_R208_FIXTURES)
    def test_parse_r208_document(self, fixture_name):
        """Test parsing R2.0.8 format document."""
        fixture_file = FIXTURES_DIR / fixture_name
        result = ted_v2.parse_xml_file(fixture_file)

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
        assert document.publication_date is not None, (
            f"Publication date should be present in {fixture_name}"
        )
        assert document.version, f"Version should be present in {fixture_name}"
        assert "R2.0.8" in document.version or "R2.0.7/R2.0.8" in document.version

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

    def test_parse_r208_procedure_type(self):
        """Test procedure_type extraction for R2.0.8."""
        fixture_file = FIXTURES_DIR / "ted_v2_r2_0_8_2015.xml"
        result = ted_v2.parse_xml_file(fixture_file)
        assert result[0].contract.procedure_type.code == "open"
        assert result[0].contract.procedure_type.description == "Open procedure"

    def test_parse_r208_contract_nature_normalized(self):
        """Test contract nature code is normalized from old '4' to 'services'."""
        fixture_file = FIXTURES_DIR / "ted_v2_r2_0_8_2015.xml"
        result = ted_v2.parse_xml_file(fixture_file)
        assert result[0].contract.contract_nature_code == "services"

    def test_parse_r208_authority_type_normalized(self):
        """Test authority type code is normalized from old '3' to 'ra'."""
        fixture_file = FIXTURES_DIR / "ted_v2_r2_0_8_2015.xml"
        result = ted_v2.parse_xml_file(fixture_file)
        cb = result[0].contracting_body
        assert cb.authority_type is not None
        assert cb.authority_type.code == "ra"
        assert cb.authority_type.description == "Regional authority"

    def test_parse_r208_cpv_codes(self):
        """Test CPV code extraction for R2.0.8: main + additional with descriptions."""
        fixture_file = FIXTURES_DIR / "ted_v2_r2_0_8_2015.xml"
        result = ted_v2.parse_xml_file(fixture_file)
        contract = result[0].contract

        assert contract.main_cpv_code == "64110000"
        assert len(contract.cpv_codes) == 2
        assert contract.cpv_codes[0].code == "64110000"
        assert contract.cpv_codes[0].description == "Postal services"
        assert contract.cpv_codes[1].code == "64113000"
        assert contract.cpv_codes[1].description == "Postal services related to parcels"


class TestTedV2R209Parser:
    """Tests for TED 2.0 R2.0.9 format parser (F03_2014 forms)."""

    def test_parse_r209_document_detailed(self):
        """Test parsing R2.0.9 format document with detailed validation (2024 fixture only)."""
        fixture_file = FIXTURES_DIR / "ted_v2_r2_0_9_2024.xml"
        result = ted_v2.parse_xml_file(fixture_file)

        # Validate result structure
        assert result is not None, "Parser should return result"
        assert isinstance(result, list)
        assert len(result) > 0, "Should extract at least one award"

        # Validate award data
        award_data = result[0]
        assert isinstance(award_data, AwardDataModel)

        # Validate document
        document = award_data.document
        assert isinstance(document, DocumentModel)
        assert document.doc_id == "002670-2024", "Document ID should match fixture"
        assert document.publication_date is not None, (
            "Publication date should be present"
        )
        assert document.publication_date == date(2024, 1, 3), (
            "Publication date should be 2024-01-03"
        )
        assert document.version == "R2.0.9", "Version should be R2.0.9"
        assert document.source_country == "AT", "Source country should be Austria"

        # Validate contracting body
        contracting_body = award_data.contracting_body
        assert isinstance(contracting_body, ContractingBodyModel)
        assert contracting_body.official_name, "Contracting body name should be present"
        assert "Medizinische Universität Innsbruck" in contracting_body.official_name
        assert contracting_body.country_code == "AT", "Country code should be Austria"
        assert contracting_body.town == "Innsbruck", "Town should be Innsbruck"
        assert contracting_body.nuts_code == "AT332", "NUTS code should be AT332"
        assert contracting_body.authority_type is not None
        assert contracting_body.authority_type.code == "body-pl"
        assert (
            contracting_body.authority_type.description == "Body governed by public law"
        )

        # Validate contract
        contract = award_data.contract
        assert isinstance(contract, ContractModel)
        assert contract.title, "Contract title should be present"
        assert "Pipettierroboter" in contract.title, (
            "Title should mention Pipettierroboter"
        )
        assert contract.nuts_code == "AT332", (
            "Performance location NUTS should be AT332"
        )
        assert contract.main_cpv_code == "38430000", "Main CPV code should match"
        assert len(contract.cpv_codes) == 1, "Should have one CPV code"
        assert contract.cpv_codes[0].code == "38430000", "CPV code should match"
        assert contract.cpv_codes[0].description == "Detection and analysis apparatus"
        assert contract.procedure_type.code == "neg-wo-call", (
            "Procedure type code should be normalized from T"
        )
        assert (
            contract.procedure_type.description
            == "Negotiated without prior call for competition"
        )

        # Validate awards
        assert len(award_data.awards) > 0, "Should have at least one award"
        award = award_data.awards[0]
        assert isinstance(award, AwardModel)
        assert award.awarded_value is not None, "Award value should be present"
        assert award.awarded_value == 388481.50, "Award value should match"
        assert award.awarded_value_currency == "EUR", "Currency should be EUR"
        assert award.tenders_received == 1, "Should have received 1 tender"

        # Validate contractors
        assert len(award.contractors) > 0, "Should have at least one contractor"
        contractor = award.contractors[0]
        assert isinstance(contractor, ContractorModel)
        assert contractor.official_name, "Contractor name should be present"
        assert "Hamilton Germany" in contractor.official_name, (
            "Contractor should be Hamilton Germany"
        )
        assert contractor.country_code == "DE", "Contractor country should be Germany"
        assert contractor.nuts_code == "DE21H", "Contractor NUTS should be DE21H"

    @pytest.mark.parametrize("fixture_name", TED_V2_R209_FIXTURES)
    def test_parse_r209_document(self, fixture_name):
        """Test parsing R2.0.9 format document (all fixtures)."""
        fixture_file = FIXTURES_DIR / fixture_name
        result = ted_v2.parse_xml_file(fixture_file)

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
        assert document.publication_date is not None, (
            f"Publication date should be present in {fixture_name}"
        )
        assert document.version == "R2.0.9", (
            f"Version should be R2.0.9 in {fixture_name}"
        )
        assert document.source_country, (
            f"Source country should be present in {fixture_name}"
        )

        # Validate contracting body
        contracting_body = award_data.contracting_body
        assert isinstance(contracting_body, ContractingBodyModel)
        assert contracting_body.official_name, (
            f"Contracting body name should be present in {fixture_name}"
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


class TestNewFields:
    """Tests for newly added fields in TED v2 parser."""

    def test_r209_award_date(self):
        """Test award_date extraction from DATE_CONCLUSION_CONTRACT."""
        fixture_file = FIXTURES_DIR / "ted_v2_r2_0_9_2024.xml"
        result = ted_v2.parse_xml_file(fixture_file)
        award = result[0].awards[0]
        assert award.award_date == date(2023, 12, 28)

    def test_r209_lot_number(self):
        """Test lot_number extraction from AWARD_CONTRACT ITEM attribute."""
        fixture_file = FIXTURES_DIR / "ted_v2_r2_0_9_2024.xml"
        result = ted_v2.parse_xml_file(fixture_file)
        award = result[0].awards[0]
        assert award.lot_number == "1"

    def test_r209_eu_not_funded(self):
        """Test eu_funded is False when NO_EU_PROGR_RELATED is present."""
        fixture_file = FIXTURES_DIR / "ted_v2_r2_0_9_2024.xml"
        result = ted_v2.parse_xml_file(fixture_file)
        assert result[0].contract.eu_funded is False

    def test_r209_framework_agreement_false(self):
        """Test framework_agreement defaults to False when no FRAMEWORK element."""
        fixture_file = FIXTURES_DIR / "ted_v2_r2_0_9_2024.xml"
        result = ted_v2.parse_xml_file(fixture_file)
        assert result[0].contract.framework_agreement is False

    def test_r207_lot_number(self):
        """Test lot_number extraction from AWARD_OF_CONTRACT ITEM attribute."""
        fixture_file = FIXTURES_DIR / "ted_v2_r2_0_7_2011.xml"
        result = ted_v2.parse_xml_file(fixture_file)
        # Fixture has 3 awards with ITEM="1", "2", "3"
        assert result[0].awards[0].lot_number == "1"
        assert result[0].awards[1].lot_number == "2"
        assert result[0].awards[2].lot_number == "3"

    def test_r207_award_date(self):
        """Test award_date extraction from CONTRACT_AWARD_DATE (nested elements)."""
        fixture_file = FIXTURES_DIR / "ted_v2_r2_0_7_2011.xml"
        result = ted_v2.parse_xml_file(fixture_file)
        award = result[0].awards[0]
        assert award.award_date == date(2010, 12, 22)

    def test_r207_eu_not_funded(self):
        """Test eu_funded is False when RELATES_TO_EU_PROJECT_NO is present."""
        fixture_file = FIXTURES_DIR / "ted_v2_r2_0_7_2011.xml"
        result = ted_v2.parse_xml_file(fixture_file)
        assert result[0].contract.eu_funded is False

    def test_r208_nationalid_contracting_body(self):
        """Test NATIONALID extraction from contracting body in R2.0.8."""
        fixture_file = FIXTURES_DIR / "ted_v2_r2_0_8_2015.xml"
        result = ted_v2.parse_xml_file(fixture_file)
        cb = result[0].contracting_body
        assert len(cb.identifiers) == 1
        assert cb.identifiers[0].scheme is None
        assert cb.identifiers[0].identifier == "233 5000 16000 40"

    def test_r208_nationalid_contractor_absent(self):
        """Test contractors without NATIONALID have empty identifiers in R2.0.8."""
        fixture_file = FIXTURES_DIR / "ted_v2_r2_0_8_2015.xml"
        result = ted_v2.parse_xml_file(fixture_file)
        contractor = result[0].awards[0].contractors[0]
        assert contractor.identifiers == []

    def test_r209_nationalid_contracting_body(self):
        """Test NATIONALID extraction from ADDRESS_CONTRACTING_BODY in R2.0.9."""
        fixture_file = FIXTURES_DIR / "ted_v2_r2_0_9_nationalid.xml"
        result = ted_v2.parse_xml_file(fixture_file)
        cb = result[0].contracting_body
        assert len(cb.identifiers) == 1
        assert cb.identifiers[0].scheme is None
        assert cb.identifiers[0].identifier == "14503401"

    def test_r209_nationalid_contractor(self):
        """Test NATIONALID extraction from ADDRESS_CONTRACTOR in R2.0.9."""
        fixture_file = FIXTURES_DIR / "ted_v2_r2_0_9_nationalid.xml"
        result = ted_v2.parse_xml_file(fixture_file)
        contractor = result[0].awards[0].contractors[0]
        assert len(contractor.identifiers) == 1
        assert contractor.identifiers[0].scheme is None
        assert contractor.identifiers[0].identifier == "RO 947730"

    def test_r209_no_nationalid(self):
        """Test documents without NATIONALID have empty identifiers."""
        fixture_file = FIXTURES_DIR / "ted_v2_r2_0_9_2024.xml"
        result = ted_v2.parse_xml_file(fixture_file)
        assert result[0].contracting_body.identifiers == []
        assert result[0].awards[0].contractors[0].identifiers == []


class TestDataValidation:
    """Tests for data validation and quality."""

    def test_date_fields_are_valid(self):
        """Test that date fields are properly validated."""
        fixture_file = FIXTURES_DIR / "ted_v2_r2_0_9_2024.xml"
        result = ted_v2.parse_xml_file(fixture_file)

        assert result is not None
        award_data = result[0]

        # Check date fields
        assert isinstance(award_data.document.publication_date, date)
        if award_data.document.dispatch_date:
            assert isinstance(award_data.document.dispatch_date, date)

    def test_country_codes_are_uppercase(self):
        """Test that country codes are normalized to uppercase."""
        fixture_file = FIXTURES_DIR / "ted_v2_r2_0_9_2024.xml"
        result = ted_v2.parse_xml_file(fixture_file)

        assert result is not None
        award_data = result[0]

        # Check country codes
        if award_data.document.source_country:
            assert award_data.document.source_country.isupper()
        if award_data.contracting_body.country_code:
            assert award_data.contracting_body.country_code.isupper()

        for award in award_data.awards:
            for contractor in award.contractors:
                if contractor.country_code:
                    assert contractor.country_code.isupper()

    def test_contractor_names_are_present(self):
        """Test that contractors have valid names."""
        fixture_file = FIXTURES_DIR / "ted_v2_r2_0_9_2024.xml"
        result = ted_v2.parse_xml_file(fixture_file)

        assert result is not None
        award_data = result[0]

        for award in award_data.awards:
            if award.contractors:
                for contractor in award.contractors:
                    assert contractor.official_name, (
                        "Contractor must have official name"
                    )
                    assert len(contractor.official_name.strip()) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
