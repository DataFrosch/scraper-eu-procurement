"""Tests for parse_monetary_value aggregator."""

from awards.parsers.monetary import parse_monetary_value


class TestParseMonetaryValue:
    """Tests for parse_monetary_value aggregator."""

    def test_dot_decimal_format(self):
        """Should match float_dot_decimal parser."""
        assert parse_monetary_value("878000.00", "test_field") == 878000.00

    def test_comma_decimal_format(self):
        """Should match float_comma_decimal parser."""
        assert parse_monetary_value("885,72", "test_field") == 885.72

    def test_space_thousands_format(self):
        """Should match float_space_thousands parser."""
        assert parse_monetary_value("878 000,00", "test_field") == 878000.00

    def test_space_thousands_no_decimal(self):
        assert parse_monetary_value("10 760 400", "test_field") == 10760400.0

    def test_integer(self):
        assert parse_monetary_value("1234", "test_field") == 1234.0

    def test_dot_decimal_1_format(self):
        """Should match float_dot_decimal_1 parser."""
        assert parse_monetary_value("979828.1", "test_field") == 979828.1

    def test_doublespace_thousands_format(self):
        """Should match float_doublespace_thousands parser."""
        assert parse_monetary_value("1 011  606,51", "test_field") == 1011606.51

    def test_doublespace_thousands_two_groups(self):
        """Should match float_doublespace_thousands parser."""
        assert parse_monetary_value("336  256,12", "test_field") == 336256.12

    def test_no_match_logs_warning(self, caplog):
        """Should log warning when no parser matches."""
        result = parse_monetary_value("año 2011: 34 993,09", "awarded_value")
        assert result is None
        assert "No monetary parser matched for awarded_value" in caplog.text

    def test_empty_string(self):
        assert parse_monetary_value("", "test_field") is None

    def test_none(self):
        assert parse_monetary_value(None, "test_field") is None

    def test_whitespace_only(self):
        assert parse_monetary_value("   ", "test_field") is None
