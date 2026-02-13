"""Tests for float_doublespace_thousands parser."""

from tedawards.parsers.monetary import parse_float_doublespace_thousands


class TestParseFloatDoublespaceThousands:
    """Tests for parse_float_doublespace_thousands."""

    def test_three_groups_doublespace_before_last(self):
        assert parse_float_doublespace_thousands("1 011  606,51") == 1011606.51

    def test_three_groups_doublespace_before_last_2(self):
        assert parse_float_doublespace_thousands("1 098  838,86") == 1098838.86

    def test_two_groups_doublespace(self):
        assert parse_float_doublespace_thousands("336  256,12") == 336256.12

    def test_rejects_single_space_thousands(self):
        """Must reject standard single-space format - use float_space_thousands."""
        assert parse_float_doublespace_thousands("1 234,56") is None

    def test_rejects_doublespace_between_first_groups(self):
        """Must reject double space in wrong position."""
        assert parse_float_doublespace_thousands("1  011 606,51") is None

    def test_rejects_no_decimal(self):
        assert parse_float_doublespace_thousands("336  256") is None

    def test_rejects_one_decimal(self):
        assert parse_float_doublespace_thousands("336  256,1") is None

    def test_rejects_three_decimals(self):
        assert parse_float_doublespace_thousands("336  256,123") is None

    def test_rejects_no_space(self):
        assert parse_float_doublespace_thousands("336256,12") is None

    def test_rejects_text(self):
        assert parse_float_doublespace_thousands("año 2011: 34 993,09") is None

    def test_empty_string(self):
        assert parse_float_doublespace_thousands("") is None

    def test_none(self):
        assert parse_float_doublespace_thousands(None) is None

    def test_whitespace_only(self):
        assert parse_float_doublespace_thousands("   ") is None
