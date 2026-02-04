"""Tests for ISO date with timezone offset parser."""

from datetime import date
from tedawards.parsers.date import parse_date_iso_offset


def test_parse_date_iso_offset():
    """Test strict ISO date with timezone offset parsing."""
    # Valid dates with positive offset
    assert parse_date_iso_offset("2025-01-02+01:00", "test_field") == date(2025, 1, 2)
    assert parse_date_iso_offset("2024-12-30+02:00", "test_field") == date(2024, 12, 30)

    # Valid dates with negative offset
    assert parse_date_iso_offset("2025-01-02-05:00", "test_field") == date(2025, 1, 2)
    assert parse_date_iso_offset("2024-06-15-08:00", "test_field") == date(2024, 6, 15)

    # Empty value
    assert parse_date_iso_offset("", "test_field") is None
    assert parse_date_iso_offset("   ", "test_field") is None


def test_parse_date_iso_offset_rejects_other_formats():
    """Test that strict parser rejects non-standard formats."""
    # Plain ISO date without offset - should be rejected
    assert parse_date_iso_offset("2025-01-02", "test_field") is None

    # ISO with Z suffix - should be rejected
    assert parse_date_iso_offset("2025-01-02Z", "test_field") is None

    # YYYYMMDD format - should be rejected
    assert parse_date_iso_offset("20250102", "test_field") is None

    # Full datetime - should be rejected
    assert parse_date_iso_offset("2025-01-02T10:30:00+01:00", "test_field") is None

    # Invalid date values
    assert parse_date_iso_offset("2025-13-02+01:00", "test_field") is None
    assert parse_date_iso_offset("2025-01-32+01:00", "test_field") is None
