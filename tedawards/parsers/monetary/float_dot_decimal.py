"""
Parser for float values with dot as decimal separator.
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


def parse_float_dot_decimal(value_str: str, field_name: str) -> Optional[float]:
    """
    Parse float with dot as decimal separator: "1234.56" or "1234"

    Only accepts: digits with optional single dot as decimal separator.
    No thousand separators, no spaces, no currency symbols.

    Returns None and logs warning if format doesn't match exactly.
    """
    if not value_str:
        return None

    stripped = value_str.strip()
    if not stripped:
        return None

    # Must match: optional digits, optional dot with digits, or just digits
    if not re.match(r"^\d+(\.\d+)?$", stripped):
        logger.warning(
            "Invalid %s: %r (expected format: digits with optional dot decimal, e.g., '1234.56')",
            field_name,
            value_str,
        )
        return None

    return float(stripped)
