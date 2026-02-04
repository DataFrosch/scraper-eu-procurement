"""
XML extraction helpers for TED parsers.
"""

import re
from datetime import date
from typing import List, Optional

from lxml import etree


def parse_date_yyyymmdd(text: str) -> date:
    """
    Parse date from YYYYMMDD format (e.g., "20081231").

    Raises ValueError if format is invalid.
    """
    if len(text) != 8:
        raise ValueError(f"Expected 8-digit date, got: {text}")
    year = int(text[0:4])
    month = int(text[4:6])
    day = int(text[6:8])
    return date(year, month, day)


def parse_iso_date(text: str) -> date:
    """
    Parse ISO date, stripping timezone suffix if present.

    Handles: "2024-01-15", "2024-01-15Z", "2024-01-15+01:00", "2024-01-15T10:30:00Z"
    Raises ValueError if format is invalid.
    """
    # Strip timezone/time suffixes
    date_only = text.split("Z")[0].split("+")[0].split("T")[0]
    return date.fromisoformat(date_only.strip())


def element_text(elem: etree._Element) -> str:
    """
    Get all text content from element and its children, stripped.

    Usage: element_text(title_elem) instead of "".join(title_elem.itertext()).strip()
    """
    return "".join(elem.itertext()).strip()


def parse_monetary_value(value_str: str) -> Optional[float]:
    """
    Parse monetary value from TED document strings.

    Handles common formats:
    - "1000.00" -> 1000.0
    - "1 000,00" -> 1000.0 (European format)
    - "1,000.00" -> 1000.0 (US format)
    """
    if not value_str:
        return None

    # Remove spaces and non-breaking spaces
    cleaned = value_str.strip().replace(" ", "").replace("\u00a0", "")

    # Handle European format (comma as decimal separator)
    # If there's exactly one comma and it's near the end, treat as decimal
    if "," in cleaned and "." not in cleaned:
        # Pure European: "1000,50"
        cleaned = cleaned.replace(",", ".")
    elif "," in cleaned and "." in cleaned:
        # Mixed: "1.000,50" (European with thousand sep) or "1,000.50" (US)
        # Check position - if comma is after last dot, it's the decimal
        last_comma = cleaned.rfind(",")
        last_dot = cleaned.rfind(".")
        if last_comma > last_dot:
            # European: "1.000,50" -> remove dots, replace comma
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            # US: "1,000.50" -> just remove commas
            cleaned = cleaned.replace(",", "")

    # Remove any remaining non-numeric characters except dots
    cleaned = re.sub(r"[^\d.]", "", cleaned)

    if not cleaned:
        return None

    try:
        return float(cleaned)
    except ValueError:
        return None


def xpath_text(element: etree._Element, xpath: str) -> str:
    """
    Extract text at xpath, returning empty string if not found.

    Appends /text() to the xpath automatically.
    """
    result = element.xpath(xpath + "/text()")
    return result[0].strip() if result and result[0] else ""


def first_text(elements: List[etree._Element]) -> Optional[str]:
    """
    Get text from first element in list, or None if empty.

    Usage: first_text(root.xpath('.//TITLE'))
    """
    if elements and elements[0].text:
        return elements[0].text.strip()
    return None


def first_attr(elements: List[etree._Element], attr: str) -> Optional[str]:
    """
    Get attribute from first element in list, or None if empty.

    Usage: first_attr(root.xpath('.//COUNTRY'), 'VALUE')
    """
    if elements:
        return elements[0].get(attr)
    return None
