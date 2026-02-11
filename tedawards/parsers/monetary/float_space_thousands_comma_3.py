"""
Parser for float values with space thousands separator and comma decimal, exactly 3 decimal digits.

Format: "56 146,820"
- Space as thousands separator
- Comma as decimal separator
- Exactly 3 decimal digits
"""

import re
from typing import Optional


def parse_float_space_thousands_comma_3(value_str: str) -> Optional[float]:
    """
    Parse float with space thousands and comma decimal, exactly 3 decimal digits.

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

    # Must match: space-separated thousands (1-3 groups) with comma and exactly 3 decimal digits
    if not re.match(r"^\d{1,3}(?: \d{3}){1,3},\d{3}$", stripped):
        return None

    # Remove spaces and replace comma with dot
    normalized = stripped.replace(" ", "").replace(",", ".")
    return float(normalized)
