"""Tests for float_comma_decimal_1 parser."""

from tedawards.parsers.monetary.float_comma_decimal_1 import parse_float_comma_decimal_1


class TestParseFloatCommaDecimal1:
    """Tests for parse_float_comma_decimal_1."""

    def test_small_value(self):
        assert parse_float_comma_decimal_1("72,8") == 72.8

    def test_larger_value(self):
        assert parse_float_comma_decimal_1("1234,5") == 1234.5

    def test_whitespace_stripped(self):
        assert parse_float_comma_decimal_1("  72,8  ") == 72.8

    def test_rejects_two_decimals(self):
        """Must reject 2 decimal digits - use float_comma_decimal."""
        assert parse_float_comma_decimal_1("72,80") is None

    def test_rejects_three_decimals(self):
        assert parse_float_comma_decimal_1("72,800") is None

    def test_rejects_no_decimal(self):
        assert parse_float_comma_decimal_1("72") is None

    def test_rejects_space_thousands(self):
        """Must reject space thousands - use float_space_thousands_comma_1."""
        assert parse_float_comma_decimal_1("9 117,5") is None

    def test_rejects_dot_decimal(self):
        assert parse_float_comma_decimal_1("72.8") is None

    def test_empty_string(self):
        assert parse_float_comma_decimal_1("") is None

    def test_none(self):
        assert parse_float_comma_decimal_1(None) is None
