"""Tests for ISO date parser."""

from datetime import date
from tedawards.parsers.date import parse_date_iso


def test_parse_date_iso():
    """Test strict ISO date parsing."""
    # Valid date
    assert parse_date_iso("2024-01-15", "test_field") == date(2024, 1, 15)
    assert parse_date_iso("2008-12-31", "test_field") == date(2008, 12, 31)

    # Empty value
    assert parse_date_iso("", "test_field") is None
    assert parse_date_iso("   ", "test_field") is None


def test_parse_date_iso_rejects_other_formats():
    """Test that strict parser rejects non-standard formats."""
    # YYYYMMDD format - should be rejected
    assert parse_date_iso("20081231", "test_field") is None

    # With timezone Z - should be rejected
    assert parse_date_iso("2024-01-15Z", "test_field") is None

    # With timezone offset - should be rejected
    assert parse_date_iso("2024-01-15+01:00", "test_field") is None

    # With time component - should be rejected
    assert parse_date_iso("2024-01-15T10:30:00", "test_field") is None

    # Full ISO datetime - should be rejected
    assert parse_date_iso("2024-01-15T10:30:00Z", "test_field") is None

    # Slash separators - should be rejected
    assert parse_date_iso("2024/01/15", "test_field") is None

    # Text
    assert parse_date_iso("invalid", "test_field") is None

    # Invalid date values
    assert parse_date_iso("2024-13-15", "test_field") is None
    assert parse_date_iso("2024-01-32", "test_field") is None
