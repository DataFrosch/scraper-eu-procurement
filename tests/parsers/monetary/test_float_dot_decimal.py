"""Tests for float dot decimal parser."""

from tedawards.parsers.monetary import parse_float_dot_decimal


def test_parse_float_dot_decimal():
    """Test strict dot-decimal value parsing."""
    # Test plain number with dot decimal
    assert parse_float_dot_decimal("16425.6", "test_field") == 16425.6

    # Test integer (no decimal)
    assert parse_float_dot_decimal("16425", "test_field") == 16425.0

    # Test empty value
    assert parse_float_dot_decimal("", "test_field") is None

    # Test None-ish
    assert parse_float_dot_decimal("   ", "test_field") is None


def test_parse_float_dot_decimal_rejects_other_formats():
    """Test that strict parser rejects non-standard formats (logs warning, returns None)."""
    # Space-separated thousands - should be rejected
    assert parse_float_dot_decimal("16 425,6", "test_field") is None

    # Comma as decimal separator - should be rejected
    assert parse_float_dot_decimal("16425,60", "test_field") is None

    # Text - should be rejected
    assert parse_float_dot_decimal("invalid", "test_field") is None

    # Currency symbol - should be rejected
    assert parse_float_dot_decimal("EUR 1000", "test_field") is None

    # Thousand separator comma - should be rejected
    assert parse_float_dot_decimal("1,000.50", "test_field") is None
