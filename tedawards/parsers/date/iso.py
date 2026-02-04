"""
Parser for dates in ISO format (YYYY-MM-DD).
"""

import logging
import re
from datetime import date
from typing import Optional

logger = logging.getLogger(__name__)


def parse_date_iso(text: str, field_name: str) -> Optional[date]:
    """
    Parse date from ISO format: "2024-01-15"

    Only accepts: exactly YYYY-MM-DD format with hyphens.
    No timezone, no time component, no other characters.

    Returns None and logs warning if format doesn't match exactly.
    """
    if not text:
        return None

    stripped = text.strip()
    if not stripped:
        return None

    # Must be exactly YYYY-MM-DD
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", stripped):
        logger.warning(
            "Invalid %s: %r (expected format: YYYY-MM-DD, e.g., '2024-01-15')",
            field_name,
            text,
        )
        return None

    try:
        return date.fromisoformat(stripped)
    except ValueError:
        logger.warning(
            "Invalid %s: %r (invalid date)",
            field_name,
            text,
        )
        return None
