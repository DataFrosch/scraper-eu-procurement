"""Tests for float space thousands parser."""

from tedawards.parsers.monetary import parse_float_space_thousands


def test_parse_float_space_thousands():
    """Test parsing numbers with space as thousands separator."""
    # Basic space-separated thousands
    assert parse_float_space_thousands("10 760 400", "test_field") == 10760400.0

    # Smaller number
    assert parse_float_space_thousands("440 000", "test_field") == 440000.0

    # With comma decimal
    assert parse_float_space_thousands("1 234,56", "test_field") == 1234.56

    # With dot decimal
    assert parse_float_space_thousands("1 234.56", "test_field") == 1234.56

    # Single group (no thousands separator needed)
    assert parse_float_space_thousands("400", "test_field") == 400.0

    # Two digits
    assert parse_float_space_thousands("50", "test_field") == 50.0

    # Empty value
    assert parse_float_space_thousands("", "test_field") is None

    # Whitespace only
    assert parse_float_space_thousands("   ", "test_field") is None


def test_parse_float_space_thousands_rejects_other_formats():
    """Test that parser rejects non-matching formats."""
    # Plain number without spaces (handled by float_dot_decimal)
    assert parse_float_space_thousands("16425.6", "test_field") is None

    # Comma as thousands separator
    assert parse_float_space_thousands("1,234,567", "test_field") is None

    # Currency symbol
    assert parse_float_space_thousands("10 760 400 EUR", "test_field") is None

    # Text
    assert parse_float_space_thousands("invalid", "test_field") is None

    # "Value:" prefix
    assert parse_float_space_thousands("Value: 10 760 400", "test_field") is None

    # Irregular spacing (not groups of 3)
    assert parse_float_space_thousands("10 76 400", "test_field") is None
