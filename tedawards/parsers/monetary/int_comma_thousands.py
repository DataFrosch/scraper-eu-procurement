"""
Parser for integer values with comma as thousands separator.

Format: "600,000" or "1,234,567"
- Comma as thousands separator
- Exactly 3 digits after each comma
- No decimal part
"""

import re
from typing import Optional


def parse_int_comma_thousands(value_str: str) -> Optional[float]:
    """
    Parse integer with comma as thousands separator.

    Returns None if format doesn't match.
    """
    if not value_str:
        return None

    stripped = value_str.strip()
    if not stripped:
        return None

    # Must match: 1-3 digits, then 1-3 groups of comma + exactly 3 digits (max 12 digits)
    if not re.match(r"^\d{1,3}(,\d{3}){1,3}$", stripped):
        return None

    # Remove commas
    return float(stripped.replace(",", ""))
