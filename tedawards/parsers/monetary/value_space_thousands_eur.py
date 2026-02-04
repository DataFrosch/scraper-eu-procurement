"""
Parser for EUR monetary values in "Value: X  EUR." format.

Format: "Value: 10 760 400  EUR."
- "Value: " prefix (required)
- Space as thousands separator
- Optional comma as decimal separator
- "  EUR." suffix with trailing dot
"""

import re
from typing import Optional


def parse_monetary_value_space_thousands_eur(
    value_str: str, field_name: str
) -> Optional[float]:
    """
    Parse EUR monetary value: "Value: 10 760 400  EUR."

    Exactly this format:
    - Starts with "Value: "
    - Number with spaces as thousands separator
    - Optional comma as decimal separator
    - Ends with "  EUR." (two spaces, EUR, dot)

    Returns None if format doesn't match.
    """
    if not value_str:
        return None

    stripped = value_str.strip()
    if not stripped:
        return None

    # Exact format: "Value: {number}  EUR."
    match = re.match(
        r"^Value:\s+(\d{1,3}(?:\s\d{3})*(?:,\d+)?)\s+EUR\.$",
        stripped,
        re.IGNORECASE,
    )
    if not match:
        return None

    number_str = match.group(1)

    # Remove spaces (thousands separator) and replace comma with dot (decimal)
    normalized = number_str.replace(" ", "").replace(",", ".")

    return float(normalized)
