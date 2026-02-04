"""
XML extraction helpers for TED parsers.
"""

from typing import List, Optional

from lxml import etree


def element_text(elem: Optional[etree._Element]) -> Optional[str]:
    """
    Get all text content from element and its children, stripped.
    Returns None if element is None.

    Usage: element_text(title_elem) instead of "".join(title_elem.itertext()).strip()
    """
    if elem is None:
        return None
    return "".join(elem.itertext()).strip()


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


def elem_text(elem: Optional[etree._Element]) -> Optional[str]:
    """
    Get text from element, or None if element is None.

    Usage: elem_text(root.find('.//TITLE'))
    """
    if elem is not None and elem.text:
        return elem.text.strip()
    return None


def elem_attr(elem: Optional[etree._Element], attr: str) -> Optional[str]:
    """
    Get attribute from element, or None if element is None.

    Usage: elem_attr(root.find('.//COUNTRY'), 'VALUE')
    """
    if elem is not None:
        return elem.get(attr)
    return None
