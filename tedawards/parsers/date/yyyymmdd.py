"""
Parser for dates in YYYYMMDD format (e.g., "20081231").
"""

import re
from datetime import date
from typing import Optional


def parse_date_yyyymmdd(text: str, field_name: str) -> Optional[date]:
    """
    Parse date from YYYYMMDD format (e.g., "20081231").

    Only accepts: exactly 8 digits representing YYYYMMDD.
    No separators, no spaces, no other characters.

    Returns None if format doesn't match or values are invalid.
    """
    if not text:
        return None

    stripped = text.strip()
    if not stripped:
        return None

    # Must be exactly 8 digits
    if not re.match(r"^\d{8}$", stripped):
        return None

    year = int(stripped[0:4])
    month = int(stripped[4:6])
    day = int(stripped[6:8])

    try:
        return date(year, month, day)
    except ValueError:
        return None
