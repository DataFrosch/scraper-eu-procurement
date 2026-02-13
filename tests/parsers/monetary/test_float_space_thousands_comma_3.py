"""Tests for float_space_thousands_comma_3 parser."""

from tedawards.parsers.monetary import parse_float_space_thousands_comma_3


class TestParseFloatSpaceThousandsComma3:
    """Tests for parse_float_space_thousands_comma_3."""

    def test_simple(self):
        assert parse_float_space_thousands_comma_3("56 146,820") == 56146.820

    def test_larger_value(self):
        assert parse_float_space_thousands_comma_3("1 234 567,890") == 1234567.890

    def test_whitespace_stripped(self):
        assert parse_float_space_thousands_comma_3("  56 146,820  ") == 56146.820

    def test_rejects_two_decimals(self):
        """Must reject 2 decimal digits - use float_space_thousands."""
        assert parse_float_space_thousands_comma_3("56 146,82") is None

    def test_rejects_one_decimal(self):
        assert parse_float_space_thousands_comma_3("56 146,8") is None

    def test_rejects_no_space(self):
        """Must reject no space."""
        assert parse_float_space_thousands_comma_3("56146,820") is None

    def test_rejects_dot_decimal(self):
        assert parse_float_space_thousands_comma_3("56 146.820") is None

    def test_rejects_no_decimal(self):
        assert parse_float_space_thousands_comma_3("56 146") is None

    def test_empty_string(self):
        assert parse_float_space_thousands_comma_3("") is None

    def test_none(self):
        assert parse_float_space_thousands_comma_3(None) is None
