"""
Monetary value parsers.

Each parser handles exactly ONE specific format and returns None if the
format doesn't match.  Formats are mutually exclusive so that
parse_monetary_value() can detect ambiguity.
"""

import logging
import re
from typing import Callable, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Individual format parsers
# ---------------------------------------------------------------------------


def parse_float_comma_decimal(value_str: str) -> Optional[float]:
    """Parse "885,72" or "1234,56" — comma decimal, exactly 2 digits."""
    if not value_str:
        return None
    stripped = value_str.strip()
    if not stripped:
        return None
    if not re.match(r"^\d+,\d{2}$", stripped):
        return None
    return float(stripped.replace(",", "."))


def parse_float_comma_decimal_1(value_str: str) -> Optional[float]:
    """Parse "72,8" or "1234,5" — comma decimal, exactly 1 digit."""
    if not value_str:
        return None
    stripped = value_str.strip()
    if not stripped:
        return None
    if not re.match(r"^\d+,\d$", stripped):
        return None
    return float(stripped.replace(",", "."))


def parse_float_comma_decimal_4(value_str: str) -> Optional[float]:
    """Parse "40,0000" or "110,0000" — comma decimal, exactly 4 digits."""
    if not value_str:
        return None
    stripped = value_str.strip()
    if not stripped:
        return None
    if not re.match(r"^\d+,\d{4}$", stripped):
        return None
    return float(stripped.replace(",", "."))


def parse_float_dot_decimal(value_str: str) -> Optional[float]:
    """Parse "1234.56" or "1234" — dot decimal (exactly 2 digits) or integer."""
    if not value_str:
        return None
    stripped = value_str.strip()
    if not stripped:
        return None
    if not re.match(r"^\d+(\.\d{2})?$", stripped):
        return None
    return float(stripped)


def parse_float_dot_decimal_1(value_str: str) -> Optional[float]:
    """Parse "979828.1" or "1684.4" — dot decimal, exactly 1 digit."""
    if not value_str:
        return None
    stripped = value_str.strip()
    if not stripped:
        return None
    if not re.match(r"^\d+\.\d$", stripped):
        return None
    return float(stripped)


def parse_float_space_thousands(value_str: str) -> Optional[float]:
    """Parse "10 760 400" or "1 234,56" — space thousands, optional 2-digit decimal."""
    if not value_str:
        return None
    stripped = value_str.strip()
    if not stripped:
        return None
    if " " not in stripped:
        return None
    if not re.match(r"^\d{1,3}(?: \d{3})*(?:[,\.]\d{2})?$", stripped):
        return None
    normalized = stripped.replace(" ", "").replace(",", ".")
    return float(normalized)


def parse_float_space_thousands_comma_1(value_str: str) -> Optional[float]:
    """Parse "9 117,5" or "617 462,5" — space thousands, comma decimal, 1 digit."""
    if not value_str:
        return None
    stripped = value_str.strip()
    if not stripped:
        return None
    if " " not in stripped:
        return None
    if not re.match(r"^\d{1,3}(?: \d{3})*,\d$", stripped):
        return None
    normalized = stripped.replace(" ", "").replace(",", ".")
    return float(normalized)


def parse_float_space_thousands_comma_3(value_str: str) -> Optional[float]:
    """Parse "56 146,820" — space thousands, comma decimal, 3 digits."""
    if not value_str:
        return None
    stripped = value_str.strip()
    if not stripped:
        return None
    if " " not in stripped:
        return None
    if not re.match(r"^\d{1,3}(?: \d{3})*,\d{3}$", stripped):
        return None
    normalized = stripped.replace(" ", "").replace(",", ".")
    return float(normalized)


def parse_float_space_thousands_comma_4(value_str: str) -> Optional[float]:
    """Parse "264 886,8600" — space thousands, comma decimal, 4 digits."""
    if not value_str:
        return None
    stripped = value_str.strip()
    if not stripped:
        return None
    if " " not in stripped:
        return None
    if not re.match(r"^\d{1,3}(?: \d{3})*,\d{4}$", stripped):
        return None
    normalized = stripped.replace(" ", "").replace(",", ".")
    return float(normalized)


def parse_float_doublespace_thousands(value_str: str) -> Optional[float]:
    """Parse "1 011  606,51" — double space before last group, comma decimal, 2 digits."""
    if not value_str:
        return None
    stripped = value_str.strip()
    if not stripped:
        return None
    if not re.match(r"^\d{1,3}(?: \d{3})*  \d{3},\d{2}$", stripped):
        return None
    result = stripped.replace(" ", "").replace(",", ".")
    return float(result)


def parse_int_comma_thousands(value_str: str) -> Optional[float]:
    """Parse "600,000" or "1,234,567" — comma thousands, no decimal."""
    if not value_str:
        return None
    stripped = value_str.strip()
    if not stripped:
        return None
    if not re.match(r"^\d{1,3}(,\d{3})+$", stripped):
        return None
    return float(stripped.replace(",", ""))


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

# Order doesn't matter since formats are mutually exclusive
_MONETARY_PARSERS: list[Callable[[str], Optional[float]]] = [
    parse_float_comma_decimal,
    parse_float_comma_decimal_1,
    parse_float_comma_decimal_4,
    parse_float_doublespace_thousands,
    parse_float_dot_decimal,
    parse_float_dot_decimal_1,
    parse_float_space_thousands,
    parse_float_space_thousands_comma_1,
    parse_float_space_thousands_comma_3,
    parse_float_space_thousands_comma_4,
    parse_int_comma_thousands,
]


def parse_monetary_value(value_str: str, field_name: str) -> Optional[float]:
    """
    Try all monetary parsers and return the parsed value.

    - Returns None if no parser matches (logs warning)
    - Returns the value if exactly one parser matches
    - Raises ValueError if multiple parsers match (indicates non-strict parsers)
    """
    if not value_str:
        return None

    stripped = value_str.strip()
    if not stripped:
        return None

    matches: list[tuple[str, float]] = []

    for parser in _MONETARY_PARSERS:
        result = parser(stripped)
        if result is not None:
            matches.append((parser.__name__, result))

    if len(matches) == 0:
        logger.warning(
            "No monetary parser matched for %s: %r",
            field_name,
            value_str,
        )
        return None
    elif len(matches) == 1:
        return matches[0][1]
    else:
        parser_names = [m[0] for m in matches]
        raise ValueError(
            f"Multiple monetary parsers matched for {field_name}: {value_str!r} "
            f"(parsers: {parser_names}). Parsers need to be more strict."
        )
