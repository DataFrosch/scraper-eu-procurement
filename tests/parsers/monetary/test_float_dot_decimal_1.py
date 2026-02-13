"""Tests for float_dot_decimal_1 parser."""

from tedawards.parsers.monetary import parse_float_dot_decimal_1


class TestParseFloatDotDecimal1:
    """Tests for parse_float_dot_decimal_1."""

    def test_one_decimal(self):
        assert parse_float_dot_decimal_1("979828.1") == 979828.1

    def test_small_number(self):
        assert parse_float_dot_decimal_1("1684.4") == 1684.4

    def test_large_number(self):
        assert parse_float_dot_decimal_1("391631.4") == 391631.4

    def test_leading_zero(self):
        assert parse_float_dot_decimal_1("0.5") == 0.5

    def test_whitespace_stripped(self):
        assert parse_float_dot_decimal_1("  114961.5  ") == 114961.5

    def test_rejects_two_decimals(self):
        """Must reject two decimal digits - handled by float_dot_decimal."""
        assert parse_float_dot_decimal_1("1234.56") is None

    def test_rejects_three_decimals(self):
        assert parse_float_dot_decimal_1("1.234") is None

    def test_rejects_integer(self):
        """Must reject integers - handled by float_dot_decimal."""
        assert parse_float_dot_decimal_1("1234") is None

    def test_rejects_comma_decimal(self):
        assert parse_float_dot_decimal_1("1234,5") is None

    def test_rejects_space_thousands(self):
        assert parse_float_dot_decimal_1("878 000.5") is None

    def test_rejects_text(self):
        assert parse_float_dot_decimal_1("abc") is None

    def test_rejects_currency_symbol(self):
        assert parse_float_dot_decimal_1("€1234.5") is None

    def test_empty_string(self):
        assert parse_float_dot_decimal_1("") is None

    def test_none(self):
        assert parse_float_dot_decimal_1(None) is None

    def test_whitespace_only(self):
        assert parse_float_dot_decimal_1("   ") is None
