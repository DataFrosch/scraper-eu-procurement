"""
Parser for dates in YYYYMMDD format (e.g., "20081231").
"""

import logging
import re
from datetime import date
from typing import Optional

logger = logging.getLogger(__name__)


def parse_date_yyyymmdd(text: str, field_name: str) -> Optional[date]:
    """
    Parse date from YYYYMMDD format (e.g., "20081231").

    Only accepts: exactly 8 digits representing YYYYMMDD.
    No separators, no spaces, no other characters.

    Returns None and logs warning if format doesn't match exactly.
    """
    if not text:
        return None

    stripped = text.strip()
    if not stripped:
        return None

    # Must be exactly 8 digits
    if not re.match(r"^\d{8}$", stripped):
        logger.warning(
            "Invalid %s: %r (expected format: YYYYMMDD, e.g., '20081231')",
            field_name,
            text,
        )
        return None

    year = int(stripped[0:4])
    month = int(stripped[4:6])
    day = int(stripped[6:8])

    try:
        return date(year, month, day)
    except ValueError:
        logger.warning(
            "Invalid %s: %r (invalid date values: year=%d, month=%d, day=%d)",
            field_name,
            text,
            year,
            month,
            day,
        )
        return None
