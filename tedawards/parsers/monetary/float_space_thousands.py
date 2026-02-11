"""
Parser for float values with space as thousands separator.

Format: "10 760 400" or "1 234,56" or "1 234.56"
- Space as thousands separator
- Optional comma or dot as decimal separator
"""

import re
from typing import Optional


def parse_float_space_thousands(value_str: str) -> Optional[float]:
    """
    Parse float with space as thousands separator: "10 760 400" or "1 234,56"

    Accepts:
    - Digits with spaces as thousands separators
    - Optional comma or dot as decimal separator
    - Must have at least one space separator (otherwise use float_dot_decimal)

    Returns None if format doesn't match.
    """
    if not value_str:
        return None

    stripped = value_str.strip()
    if not stripped:
        return None

    # Must have at least one space to qualify as this format
    if " " not in stripped:
        return None

    # Must match: digits with space-separated groups, optional decimal part (exactly 2 decimal places)
    # Examples: "10 760 400", "1 234,56", "1 234.56", "400 000"
    # Pattern: starts with 1-3 digits, then groups of space + 3 digits, optional decimal
    if not re.match(r"^\d{1,3}(?: \d{3})*(?:[,\.]\d{2})?$", stripped):
        return None

    # Remove spaces (thousands separator)
    no_spaces = stripped.replace(" ", "")

    # Replace comma with dot for decimal
    normalized = no_spaces.replace(",", ".")

    return float(normalized)
