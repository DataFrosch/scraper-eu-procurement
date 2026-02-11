"""
Parser for float values with comma as decimal separator, exactly 4 decimal digits.

Format: "40,0000" or "110,0000"
- No thousands separators
- Comma as decimal separator
- Exactly 4 decimal digits
"""

import re
from typing import Optional


def parse_float_comma_decimal_4(value_str: str) -> Optional[float]:
    """
    Parse float with comma as decimal separator and exactly 4 decimal digits.

    Returns None if format doesn't match.
    """
    if not value_str:
        return None

    stripped = value_str.strip()
    if not stripped:
        return None

    # Must match: digits with comma and exactly 4 decimal digits
    if not re.match(r"^\d+,\d{4}$", stripped):
        return None

    return float(stripped.replace(",", "."))
