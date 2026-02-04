"""Tests for Value: X EUR. format parser."""

from tedawards.parsers.monetary import parse_monetary_value_space_thousands_eur


def test_parse_monetary_value_space_thousands_eur():
    """Test parsing 'Value: X  EUR.' format."""
    # Standard format from TED META XML
    assert (
        parse_monetary_value_space_thousands_eur(
            "Value: 10 760 400  EUR.", "test_field"
        )
        == 10760400.0
    )

    # Smaller value
    assert (
        parse_monetary_value_space_thousands_eur("Value: 440 000  EUR.", "test_field")
        == 440000.0
    )

    # Single space before EUR (flexible whitespace)
    assert (
        parse_monetary_value_space_thousands_eur("Value: 50 000 EUR.", "test_field")
        == 50000.0
    )

    # With comma decimal
    assert (
        parse_monetary_value_space_thousands_eur("Value: 1 234,56  EUR.", "test_field")
        == 1234.56
    )

    # Small number (no thousands separator)
    assert (
        parse_monetary_value_space_thousands_eur("Value: 500  EUR.", "test_field")
        == 500.0
    )

    # Zero with decimals
    assert (
        parse_monetary_value_space_thousands_eur("Value: 0,00  EUR.", "test_field")
        == 0.0
    )

    # Empty value
    assert parse_monetary_value_space_thousands_eur("", "test_field") is None

    # Whitespace only
    assert parse_monetary_value_space_thousands_eur("   ", "test_field") is None


def test_parse_monetary_value_space_thousands_eur_rejects_other_formats():
    """Test that parser rejects non-matching formats."""
    # Missing "Value:" prefix
    assert (
        parse_monetary_value_space_thousands_eur("10 760 400  EUR.", "test_field")
        is None
    )

    # Missing trailing dot
    assert (
        parse_monetary_value_space_thousands_eur("Value: 10 760 400  EUR", "test_field")
        is None
    )

    # Different prefix
    assert (
        parse_monetary_value_space_thousands_eur(
            "Total: 10 760 400  EUR.", "test_field"
        )
        is None
    )

    # Euro symbol instead of EUR
    assert (
        parse_monetary_value_space_thousands_eur("Value: 10 760 400  €.", "test_field")
        is None
    )

    # Plain number (no Value: prefix, no EUR suffix)
    assert parse_monetary_value_space_thousands_eur("10760400", "test_field") is None

    # Different currency
    assert (
        parse_monetary_value_space_thousands_eur(
            "Value: 10 760 400  USD.", "test_field"
        )
        is None
    )

    # Text
    assert parse_monetary_value_space_thousands_eur("invalid", "test_field") is None

    # Estimated cost format (different prefix)
    assert (
        parse_monetary_value_space_thousands_eur(
            "Estimated cost excluding VAT: 160 000  EUR.", "test_field"
        )
        is None
    )
