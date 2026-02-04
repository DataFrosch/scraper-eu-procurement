"""Tests for YYYYMMDD date parser."""

from datetime import date
from tedawards.parsers.date import parse_date_yyyymmdd


def test_parse_date_yyyymmdd():
    """Test strict YYYYMMDD date parsing."""
    # Valid date
    assert parse_date_yyyymmdd("20081231", "test_field") == date(2008, 12, 31)
    assert parse_date_yyyymmdd("20240115", "test_field") == date(2024, 1, 15)

    # Empty value
    assert parse_date_yyyymmdd("", "test_field") is None
    assert parse_date_yyyymmdd("   ", "test_field") is None


def test_parse_date_yyyymmdd_rejects_other_formats():
    """Test that strict parser rejects non-standard formats."""
    # ISO format - should be rejected
    assert parse_date_yyyymmdd("2008-12-31", "test_field") is None

    # Too short
    assert parse_date_yyyymmdd("2008123", "test_field") is None

    # Too long
    assert parse_date_yyyymmdd("200812311", "test_field") is None

    # With separators
    assert parse_date_yyyymmdd("2008/12/31", "test_field") is None

    # Text
    assert parse_date_yyyymmdd("invalid", "test_field") is None

    # Invalid date values (month 13)
    assert parse_date_yyyymmdd("20081331", "test_field") is None

    # Invalid date values (day 32)
    assert parse_date_yyyymmdd("20081232", "test_field") is None
