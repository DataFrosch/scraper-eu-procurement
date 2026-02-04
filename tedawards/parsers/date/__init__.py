"""
Date parsers.

Each parser handles exactly ONE specific format.
"""

import logging
from datetime import date
from typing import Callable, Optional

from .yyyymmdd import parse_date_yyyymmdd
from .iso import parse_date_iso
from .iso_offset import parse_date_iso_offset

logger = logging.getLogger(__name__)

__all__ = [
    "parse_date_yyyymmdd",
    "parse_date_iso",
    "parse_date_iso_offset",
    "parse_date",
]

# All available date parsers - order doesn't matter since formats are mutually exclusive
_DATE_PARSERS: list[Callable[[str, str], Optional[date]]] = [
    parse_date_yyyymmdd,
    parse_date_iso,
    parse_date_iso_offset,
]


def parse_date(text: str, field_name: str) -> Optional[date]:
    """
    Try all date parsers and return the parsed value.

    - Returns None if no parser matches (logs warning)
    - Returns the value if exactly one parser matches
    - Raises ValueError if multiple parsers match (indicates non-strict parsers)
    """
    if not text:
        return None

    stripped = text.strip()
    if not stripped:
        return None

    matches: list[tuple[str, date]] = []

    for parser in _DATE_PARSERS:
        result = parser(stripped, field_name)
        if result is not None:
            matches.append((parser.__name__, result))

    if len(matches) == 0:
        logger.warning(
            "No date parser matched for %s: %r",
            field_name,
            text,
        )
        return None
    elif len(matches) == 1:
        return matches[0][1]
    else:
        parser_names = [m[0] for m in matches]
        raise ValueError(
            f"Multiple date parsers matched for {field_name}: {text!r} "
            f"(parsers: {parser_names}). Parsers need to be more strict."
        )
