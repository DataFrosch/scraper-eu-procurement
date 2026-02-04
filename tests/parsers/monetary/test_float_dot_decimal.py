"""Tests for float_dot_decimal parser."""

from tedawards.parsers.monetary.float_dot_decimal import parse_float_dot_decimal


class TestParseFloatDotDecimal:
    """Tests for parse_float_dot_decimal."""

    def test_integer(self):
        assert parse_float_dot_decimal("1234") == 1234.0

    def test_decimal(self):
        assert parse_float_dot_decimal("1234.56") == 1234.56

    def test_large_number(self):
        assert parse_float_dot_decimal("878000.00") == 878000.00

    def test_leading_zeros(self):
        assert parse_float_dot_decimal("0.50") == 0.50

    def test_rejects_one_decimal(self):
        """Must reject single decimal digit - ambiguous with thousands."""
        assert parse_float_dot_decimal("1234.5") is None

    def test_rejects_three_decimals(self):
        """Must reject three decimal digits - ambiguous with thousands."""
        assert parse_float_dot_decimal("1.234") is None

    def test_whitespace_stripped(self):
        assert parse_float_dot_decimal("  1234.56  ") == 1234.56

    def test_rejects_space_thousands(self):
        """Must reject European format with spaces."""
        assert parse_float_dot_decimal("878 000,00") is None

    def test_rejects_comma_decimal(self):
        """Must reject comma as decimal separator."""
        assert parse_float_dot_decimal("1234,56") is None

    def test_rejects_text(self):
        assert parse_float_dot_decimal("año 2011: 34 993,09") is None

    def test_rejects_currency_symbol(self):
        assert parse_float_dot_decimal("€1234.56") is None

    def test_empty_string(self):
        assert parse_float_dot_decimal("") is None

    def test_none(self):
        assert parse_float_dot_decimal(None) is None

    def test_whitespace_only(self):
        assert parse_float_dot_decimal("   ") is None
