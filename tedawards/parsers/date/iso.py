"""
Parser for dates in ISO format (YYYY-MM-DD).
"""

import re
from datetime import date
from typing import Optional


def parse_date_iso(text: str, field_name: str) -> Optional[date]:
    """
    Parse date from ISO format: "2024-01-15"

    Only accepts: exactly YYYY-MM-DD format with hyphens.
    No timezone, no time component, no other characters.

    Returns None if format doesn't match or date is invalid.
    """
    if not text:
        return None

    stripped = text.strip()
    if not stripped:
        return None

    # Must be exactly YYYY-MM-DD
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", stripped):
        return None

    try:
        return date.fromisoformat(stripped)
    except ValueError:
        return None
