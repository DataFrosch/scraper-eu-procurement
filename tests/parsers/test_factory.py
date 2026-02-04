"""
Tests for parser factory auto-detection.

The factory automatically detects and selects the appropriate parser
based on the file format. These tests validate:
1. Correct parser detection for all supported formats
2. Priority order (TED 2.0 -> eForms UBL)
3. Support for .xml files
"""

import pytest
from pathlib import Path

from tedawards.parsers import (
    get_parser,
    get_supported_formats,
    ted_v2,
    eforms_ubl,
)


FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"

TED_V2_R207_FIXTURES = [
    "ted_v2_r2_0_7_2011.xml",
]

TED_V2_R208_FIXTURES = [
    "ted_v2_r2_0_8_2015.xml",
]

TED_V2_R209_FIXTURES = [
    "ted_v2_r2_0_9_2024.xml",
]

EFORMS_UBL_FIXTURES = [
    "eforms_ubl_2025.xml",
    "eforms_ubl_2025_alt.xml",
]


class TestParserFactory:
    """Tests for parser factory auto-detection."""

    @pytest.mark.parametrize("fixture_name", TED_V2_R207_FIXTURES)
    def test_factory_detects_ted_v2_r207(self, fixture_name):
        """Test factory auto-detects TED 2.0 R2.0.7 format."""
        fixture_file = FIXTURES_DIR / fixture_name
        parser = get_parser(fixture_file)
        assert parser is not None, f"Factory should return a parser for {fixture_name}"
        assert parser is ted_v2, f"Should detect TED V2 parser for {fixture_name}"

    @pytest.mark.parametrize("fixture_name", TED_V2_R208_FIXTURES)
    def test_factory_detects_ted_v2_r208(self, fixture_name):
        """Test factory auto-detects TED 2.0 R2.0.8 format."""
        fixture_file = FIXTURES_DIR / fixture_name
        parser = get_parser(fixture_file)
        assert parser is not None, f"Factory should return a parser for {fixture_name}"
        assert parser is ted_v2, f"Should detect TED V2 parser for {fixture_name}"

    @pytest.mark.parametrize("fixture_name", TED_V2_R209_FIXTURES)
    def test_factory_detects_ted_v2_r209(self, fixture_name):
        """Test factory auto-detects TED 2.0 R2.0.9 format."""
        fixture_file = FIXTURES_DIR / fixture_name
        parser = get_parser(fixture_file)
        assert parser is not None, f"Factory should return a parser for {fixture_name}"
        assert parser is ted_v2, f"Should detect TED V2 parser for {fixture_name}"

    @pytest.mark.parametrize("fixture_name", EFORMS_UBL_FIXTURES)
    def test_factory_detects_eforms_ubl(self, fixture_name):
        """Test factory auto-detects eForms UBL format."""
        fixture_file = FIXTURES_DIR / fixture_name
        parser = get_parser(fixture_file)
        assert parser is not None, f"Factory should return a parser for {fixture_name}"
        assert parser is eforms_ubl, (
            f"Should detect eForms UBL parser for {fixture_name}"
        )

    def test_factory_supported_formats(self):
        """Test factory returns list of supported formats."""
        formats = get_supported_formats()
        assert len(formats) == 2, "Should support 2 formats"
        assert "TED 2.0" in formats
        assert "eForms UBL ContractAwardNotice" in formats


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
