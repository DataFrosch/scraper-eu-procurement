"""
Parser for float values with dot as decimal separator.

Format: "1234.56" or "1234"
- No thousands separators
- Dot as decimal separator
"""

import re
from typing import Optional


def parse_float_dot_decimal(value_str: str) -> Optional[float]:
    """
    Parse float with dot as decimal separator: "1234.56" or "1234"

    Only accepts: digits with optional single dot as decimal separator.
    No thousand separators, no spaces, no currency symbols.

    Returns None if format doesn't match.
    """
    if not value_str:
        return None

    stripped = value_str.strip()
    if not stripped:
        return None

    # Must match: digits with optional dot decimal (exactly 2 decimal places)
    if not re.match(r"^\d+(\.\d{2})?$", stripped):
        return None

    return float(stripped)
