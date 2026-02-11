"""
Parser for float values with dot as decimal separator, exactly 1 decimal digit.

Format: "979828.1" or "1684.4"
- No thousands separators
- Dot as decimal separator
- Exactly 1 decimal digit
"""

import re
from typing import Optional


def parse_float_dot_decimal_1(value_str: str) -> Optional[float]:
    """
    Parse float with dot as decimal separator and exactly 1 decimal digit.

    Returns None if format doesn't match.
    """
    if not value_str:
        return None

    stripped = value_str.strip()
    if not stripped:
        return None

    # Must match: digits with dot and exactly 1 decimal digit
    if not re.match(r"^\d+\.\d$", stripped):
        return None

    return float(stripped)
