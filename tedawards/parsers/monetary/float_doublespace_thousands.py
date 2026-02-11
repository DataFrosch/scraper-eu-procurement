"""
Parser for float values with double space before the last thousands group.

Format: "1 011  606,51" or "336  256,12"
- Single spaces between thousands groups, except double space before the last group
- Comma as decimal separator
- Exactly 2 decimal digits
"""

import re
from typing import Optional


def parse_float_doublespace_thousands(value_str: str) -> Optional[float]:
    """
    Parse float with double space before the last thousands group: "1 011  606,51"

    Accepts:
    - Optional leading groups of 1-3 digits separated by single spaces
    - Double space before the final 3-digit group
    - Comma as decimal separator with exactly 2 decimal digits

    Examples: "1 011  606,51", "1 098  838,86", "336  256,12"

    Returns None if format doesn't match.
    """
    if not value_str:
        return None

    stripped = value_str.strip()
    if not stripped:
        return None

    # Strict format: optional single-space-separated groups, then double space before last group
    # Examples: "336  256,12", "1 011  606,51"
    if not re.match(r"^\d{1,3}(?: \d{3})*  \d{3},\d{2}$", stripped):
        return None

    # Remove all spaces and replace comma with dot
    result = stripped.replace(" ", "").replace(",", ".")
    return float(result)
