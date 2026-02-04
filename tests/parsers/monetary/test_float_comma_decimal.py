"""Tests for float_comma_decimal parser."""

from tedawards.parsers.monetary.float_comma_decimal import parse_float_comma_decimal


class TestParseFloatCommaDecimal:
    """Tests for parse_float_comma_decimal."""

    def test_small_value(self):
        assert parse_float_comma_decimal("885,72") == 885.72

    def test_larger_value(self):
        assert parse_float_comma_decimal("1234,56") == 1234.56

    def test_rejects_single_decimal_digit(self):
        """Must reject single decimal digit - not standard currency format."""
        assert parse_float_comma_decimal("100,5") is None

    def test_rejects_three_decimal_digits(self):
        """Must reject three decimal digits - ambiguous with thousands."""
        assert parse_float_comma_decimal("1,234") is None

    def test_whitespace_stripped(self):
        assert parse_float_comma_decimal("  885,72  ") == 885.72

    def test_rejects_no_comma(self):
        """Must reject integers - use float_dot_decimal for those."""
        assert parse_float_comma_decimal("1234") is None

    def test_rejects_dot_decimal(self):
        """Must reject dot decimal - use float_dot_decimal for those."""
        assert parse_float_comma_decimal("1234.56") is None

    def test_rejects_space_thousands(self):
        """Must reject European format with spaces - use float_space_thousands."""
        assert parse_float_comma_decimal("1 234,56") is None

    def test_rejects_text(self):
        assert parse_float_comma_decimal("año 2011") is None

    def test_empty_string(self):
        assert parse_float_comma_decimal("") is None

    def test_none(self):
        assert parse_float_comma_decimal(None) is None

    def test_whitespace_only(self):
        assert parse_float_comma_decimal("   ") is None
