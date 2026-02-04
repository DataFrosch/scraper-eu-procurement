"""Tests for int_comma_thousands parser."""

from tedawards.parsers.monetary.int_comma_thousands import parse_int_comma_thousands


class TestParseIntCommaThousands:
    """Tests for parse_int_comma_thousands."""

    def test_simple(self):
        assert parse_int_comma_thousands("600,000") == 600000.0

    def test_small(self):
        assert parse_int_comma_thousands("2,949") == 2949.0

    def test_medium(self):
        assert parse_int_comma_thousands("114,800") == 114800.0

    def test_millions(self):
        assert parse_int_comma_thousands("1,234,567") == 1234567.0

    def test_billions(self):
        assert parse_int_comma_thousands("1,234,567,890") == 1234567890.0

    def test_whitespace_stripped(self):
        assert parse_int_comma_thousands("  600,000  ") == 600000.0

    def test_rejects_no_comma(self):
        """Must reject plain integers - use float_dot_decimal."""
        assert parse_int_comma_thousands("600000") is None

    def test_rejects_single_group(self):
        """Must have at least one comma group."""
        assert parse_int_comma_thousands("600") is None

    def test_rejects_decimal(self):
        """Must reject values with decimals."""
        assert parse_int_comma_thousands("600,000.50") is None

    def test_rejects_irregular_grouping(self):
        """Must reject irregular comma placement."""
        assert parse_int_comma_thousands("60,00") is None
        assert parse_int_comma_thousands("6000,000") is None

    def test_rejects_space_thousands(self):
        """Must reject space thousands format."""
        assert parse_int_comma_thousands("600 000") is None

    def test_empty_string(self):
        assert parse_int_comma_thousands("") is None

    def test_none(self):
        assert parse_int_comma_thousands(None) is None
