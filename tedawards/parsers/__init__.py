"""
TED XML parsers for contract award notices.
"""

from pathlib import Path
from typing import List, Optional

from ..schema import TedAwardDataModel
from . import ted_v2, eforms_ubl


def try_parse_award(file_path: Path) -> Optional[List[TedAwardDataModel]]:
    """Parse file if it's an award notice, return None otherwise.

    Reads first 3KB to detect format, then delegates to appropriate parser.
    """
    with open(file_path, "rb") as f:
        header = f.read(3000).decode("utf-8", errors="ignore")

    # eForms: root element tells us document type directly
    if "<ContractAwardNotice" in header:
        return eforms_ubl.parse_xml_file(file_path)

    # TED 2.0: check root + document type code 7 (Contract award)
    if "<TED_EXPORT" in header and 'CODE="7"' in header:
        return ted_v2.parse_xml_file(file_path)

    return None


__all__ = ["try_parse_award"]
