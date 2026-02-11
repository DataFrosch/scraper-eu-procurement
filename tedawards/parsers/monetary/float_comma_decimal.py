"""
Parser for float values with comma as decimal separator.

Format: "885,72" or "1234,56"
- No thousands separators
- Comma as decimal separator
"""

import re
from typing import Optional


def parse_float_comma_decimal(value_str: str) -> Optional[float]:
    """
    Parse float with comma as decimal separator: "885,72" or "1234,56"

    Only accepts: digits with single comma as decimal separator.
    No thousand separators, no spaces.

    Returns None if format doesn't match.
    """
    if not value_str:
        return None

    stripped = value_str.strip()
    if not stripped:
        return None

    # Must match: digits with comma decimal (exactly 2 decimal places)
    # Must have a comma (otherwise float_dot_decimal handles it)
    if not re.match(r"^\d+,\d{2}$", stripped):
        return None

    # Replace comma with dot for float conversion
    return float(stripped.replace(",", "."))
