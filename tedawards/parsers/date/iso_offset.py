"""
Parser for dates in ISO format with timezone offset (YYYY-MM-DD+HH:MM or YYYY-MM-DD-HH:MM).
"""

import re
from datetime import date
from typing import Optional


def parse_date_iso_offset(text: str, field_name: str) -> Optional[date]:
    """
    Parse date from ISO format with timezone offset: "2025-01-02+01:00" or "2025-01-02-05:00"

    Only accepts: YYYY-MM-DD followed by + or - and timezone offset HH:MM.
    Extracts just the date portion, discarding the timezone.

    Returns None if format doesn't match or date is invalid.
    """
    if not text:
        return None

    stripped = text.strip()
    if not stripped:
        return None

    # Must be exactly YYYY-MM-DD+HH:MM or YYYY-MM-DD-HH:MM
    if not re.match(r"^\d{4}-\d{2}-\d{2}[+-]\d{2}:\d{2}$", stripped):
        return None

    # Extract just the date part (first 10 characters)
    date_part = stripped[:10]

    try:
        return date.fromisoformat(date_part)
    except ValueError:
        return None
