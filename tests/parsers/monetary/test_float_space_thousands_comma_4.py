"""Tests for float_space_thousands_comma_4 parser."""

from awards.parsers.monetary import parse_float_space_thousands_comma_4


class TestParseFloatSpaceThousandsComma4:
    """Tests for parse_float_space_thousands_comma_4."""

    def test_simple(self):
        assert parse_float_space_thousands_comma_4("264 886,8600") == 264886.86

    def test_larger_value(self):
        assert parse_float_space_thousands_comma_4("2 208 170,7600") == 2208170.76

    def test_small_value(self):
        assert parse_float_space_thousands_comma_4("3 662,6900") == 3662.69

    def test_whitespace_stripped(self):
        assert parse_float_space_thousands_comma_4("  81 077,5400  ") == 81077.54

    def test_rejects_two_decimals(self):
        """Must reject 2 decimal digits - use float_space_thousands."""
        assert parse_float_space_thousands_comma_4("56 146,82") is None

    def test_rejects_three_decimals(self):
        assert parse_float_space_thousands_comma_4("56 146,820") is None

    def test_rejects_one_decimal(self):
        assert parse_float_space_thousands_comma_4("56 146,8") is None

    def test_rejects_no_space(self):
        assert parse_float_space_thousands_comma_4("264886,8600") is None

    def test_rejects_dot_decimal(self):
        assert parse_float_space_thousands_comma_4("56 146.8600") is None

    def test_rejects_no_decimal(self):
        assert parse_float_space_thousands_comma_4("56 146") is None

    def test_empty_string(self):
        assert parse_float_space_thousands_comma_4("") is None

    def test_none(self):
        assert parse_float_space_thousands_comma_4(None) is None
