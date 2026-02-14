"""Tests for float_space_thousands parser."""

from awards.parsers.monetary import parse_float_space_thousands


class TestParseFloatSpaceThousands:
    """Tests for parse_float_space_thousands."""

    def test_thousands_no_decimal(self):
        assert parse_float_space_thousands("10 760 400") == 10760400.0

    def test_thousands_with_comma_decimal(self):
        assert parse_float_space_thousands("1 234,56") == 1234.56

    def test_thousands_with_dot_decimal(self):
        assert parse_float_space_thousands("1 234.56") == 1234.56

    def test_simple_thousands(self):
        assert parse_float_space_thousands("400 000") == 400000.0

    def test_european_format(self):
        assert parse_float_space_thousands("878 000,00") == 878000.00

    def test_whitespace_stripped(self):
        assert parse_float_space_thousands("  1 234,56  ") == 1234.56

    def test_rejects_no_space(self):
        """Must reject numbers without space separator - use float_dot_decimal instead."""
        assert parse_float_space_thousands("1234.56") is None

    def test_rejects_text_with_numbers(self):
        """Must reject text containing numbers."""
        assert parse_float_space_thousands("año 2011: 34 993,09") is None

    def test_rejects_multiple_values(self):
        """Must reject multiple values separated by semicolon."""
        assert parse_float_space_thousands("34 993,09; 69 986,18") is None

    def test_rejects_irregular_spacing(self):
        """Must reject numbers with irregular spacing."""
        assert parse_float_space_thousands("12 34,56") is None

    def test_rejects_one_decimal(self):
        """Must reject single decimal digit."""
        assert parse_float_space_thousands("1 234,5") is None

    def test_rejects_three_decimals(self):
        """Must reject three decimal digits."""
        assert parse_float_space_thousands("1 234,567") is None

    def test_empty_string(self):
        assert parse_float_space_thousands("") is None

    def test_none(self):
        assert parse_float_space_thousands(None) is None

    def test_whitespace_only(self):
        assert parse_float_space_thousands("   ") is None
