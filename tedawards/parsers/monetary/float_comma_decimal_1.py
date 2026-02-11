"""
Parser for float values with comma as decimal separator, exactly 1 decimal digit.

Format: "72,8" or "1234,5"
- No thousands separators
- Comma as decimal separator
- Exactly 1 decimal digit
"""

import re
from typing import Optional


def parse_float_comma_decimal_1(value_str: str) -> Optional[float]:
    """
    Parse float with comma as decimal separator and exactly 1 decimal digit.

    Returns None if format doesn't match.
    """
    if not value_str:
        return None

    stripped = value_str.strip()
    if not stripped:
        return None

    # Must match: digits with comma and exactly 1 decimal digit
    if not re.match(r"^\d+,\d$", stripped):
        return None

    return float(stripped.replace(",", "."))
