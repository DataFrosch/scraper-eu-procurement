"""Tests for float_comma_decimal_4 parser."""

from tedawards.parsers.monetary.float_comma_decimal_4 import (
    parse_float_comma_decimal_4,
)


class TestParseFloatCommaDecimal4:
    """Tests for parse_float_comma_decimal_4."""

    def test_small_value(self):
        assert parse_float_comma_decimal_4("40,0000") == 40.0

    def test_another_value(self):
        assert parse_float_comma_decimal_4("49,0000") == 49.0

    def test_larger_value(self):
        assert parse_float_comma_decimal_4("110,0000") == 110.0

    def test_with_nonzero_decimals(self):
        assert parse_float_comma_decimal_4("85,5000") == 85.5

    def test_all_nonzero_decimals(self):
        assert parse_float_comma_decimal_4("1234,5678") == 1234.5678

    def test_whitespace_stripped(self):
        assert parse_float_comma_decimal_4("  40,0000  ") == 40.0

    def test_rejects_two_decimals(self):
        """Must reject 2 decimal digits - use float_comma_decimal."""
        assert parse_float_comma_decimal_4("885,72") is None

    def test_rejects_one_decimal(self):
        assert parse_float_comma_decimal_4("100,5") is None

    def test_rejects_three_decimals(self):
        assert parse_float_comma_decimal_4("1,234") is None

    def test_rejects_space_thousands(self):
        """Must reject space-separated thousands - use float_space_thousands_comma_4."""
        assert parse_float_comma_decimal_4("264 886,8600") is None

    def test_rejects_dot_decimal(self):
        assert parse_float_comma_decimal_4("1234.5678") is None

    def test_rejects_no_comma(self):
        assert parse_float_comma_decimal_4("1234") is None

    def test_rejects_text(self):
        assert parse_float_comma_decimal_4("año 2011") is None

    def test_empty_string(self):
        assert parse_float_comma_decimal_4("") is None

    def test_none(self):
        assert parse_float_comma_decimal_4(None) is None

    def test_whitespace_only(self):
        assert parse_float_comma_decimal_4("   ") is None
