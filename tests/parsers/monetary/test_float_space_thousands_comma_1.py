"""Tests for float_space_thousands_comma_1 parser."""

from tedawards.parsers.monetary import parse_float_space_thousands_comma_1


class TestParseFloatSpaceThousandsComma1:
    """Tests for parse_float_space_thousands_comma_1."""

    def test_simple(self):
        assert parse_float_space_thousands_comma_1("9 117,5") == 9117.5

    def test_larger_value(self):
        assert parse_float_space_thousands_comma_1("617 462,5") == 617462.5

    def test_millions(self):
        assert parse_float_space_thousands_comma_1("1 234 567,8") == 1234567.8

    def test_whitespace_stripped(self):
        assert parse_float_space_thousands_comma_1("  9 117,5  ") == 9117.5

    def test_rejects_two_decimals(self):
        """Must reject 2 decimal digits - use float_space_thousands."""
        assert parse_float_space_thousands_comma_1("9 117,50") is None

    def test_rejects_three_decimals(self):
        assert parse_float_space_thousands_comma_1("9 117,500") is None

    def test_rejects_no_space(self):
        """Must reject no space - use float_comma_decimal_1."""
        assert parse_float_space_thousands_comma_1("9117,5") is None

    def test_rejects_dot_decimal(self):
        assert parse_float_space_thousands_comma_1("9 117.5") is None

    def test_rejects_no_decimal(self):
        assert parse_float_space_thousands_comma_1("9 117") is None

    def test_empty_string(self):
        assert parse_float_space_thousands_comma_1("") is None

    def test_none(self):
        assert parse_float_space_thousands_comma_1(None) is None
