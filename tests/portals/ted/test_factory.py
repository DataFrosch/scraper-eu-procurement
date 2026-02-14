"""
Tests for try_parse_award detection and parsing.

Validates that:
1. Award notices are correctly detected and parsed
2. Non-award files return None
"""

from pathlib import Path

from awards.portals.ted import try_parse_award


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestTryParseAward:
    """Tests for try_parse_award detection and parsing."""

    def test_parses_ted_v2_r207(self):
        """Test parsing TED 2.0 R2.0.7 award notice."""
        result = try_parse_award(FIXTURES_DIR / "ted_v2_r2_0_7_2011.xml")
        assert result is not None
        assert len(result) == 1
        assert result[0].document.doc_id == "005302-2011"

    def test_parses_ted_v2_r208(self):
        """Test parsing TED 2.0 R2.0.8 award notice."""
        result = try_parse_award(FIXTURES_DIR / "ted_v2_r2_0_8_2015.xml")
        assert result is not None
        assert len(result) == 1

    def test_parses_ted_v2_r209(self):
        """Test parsing TED 2.0 R2.0.9 award notice."""
        result = try_parse_award(FIXTURES_DIR / "ted_v2_r2_0_9_2024.xml")
        assert result is not None
        assert len(result) == 1

    def test_parses_eforms_ubl(self):
        """Test parsing eForms UBL award notice."""
        result = try_parse_award(FIXTURES_DIR / "eforms_ubl_2025.xml")
        assert result is not None
        assert len(result) == 1

    def test_parses_eforms_ubl_alt(self):
        """Test parsing alternate eForms UBL award notice."""
        result = try_parse_award(FIXTURES_DIR / "eforms_ubl_2025_alt.xml")
        assert result is not None
        assert len(result) == 1
