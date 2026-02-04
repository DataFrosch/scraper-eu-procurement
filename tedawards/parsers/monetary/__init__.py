"""
Monetary value parsers.

Each parser handles exactly ONE specific format.
"""

import logging
from typing import Callable, Optional

from .float_comma_decimal import parse_float_comma_decimal
from .float_dot_decimal import parse_float_dot_decimal
from .float_space_thousands import parse_float_space_thousands

logger = logging.getLogger(__name__)

__all__ = [
    "parse_float_comma_decimal",
    "parse_float_dot_decimal",
    "parse_float_space_thousands",
    "parse_monetary_value",
]

# All available monetary parsers - order doesn't matter since formats are mutually exclusive
_MONETARY_PARSERS: list[Callable[[str], Optional[float]]] = [
    parse_float_comma_decimal,
    parse_float_dot_decimal,
    parse_float_space_thousands,
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
