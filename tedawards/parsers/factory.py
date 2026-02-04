"""
Parser factory for selecting appropriate parser for different TED XML formats.
"""

from pathlib import Path
from types import ModuleType
from typing import List, Optional

from ..schema import TedAwardDataModel
from . import ted_meta_xml, ted_internal_ojs, ted_v2, eforms_ubl

# Parser modules in priority order
PARSERS: List[ModuleType] = [
    ted_meta_xml,  # Try META XML format first (for legacy 2008-2013 data in ZIP files)
    ted_internal_ojs,  # INTERNAL_OJS R2.0.5 (2008 .en files)
    ted_v2,  # Unified TED 2.0 parser (R2.0.7, R2.0.8, R2.0.9)
    eforms_ubl,  # eForms UBL (2024+)
]


def get_parser(file_path: Path) -> Optional[ModuleType]:
    """Get the appropriate parser module for the given file."""
    for parser in PARSERS:
        if parser.can_parse(file_path):
            return parser
    return None


def parse_file(file_path: Path) -> Optional[List[TedAwardDataModel]]:
    """Parse file using the appropriate parser."""
    parser = get_parser(file_path)
    if parser is None:
        return None
    return parser.parse_xml_file(file_path)


def get_supported_formats() -> List[str]:
    """Get list of supported format names."""
    return [parser.get_format_name() for parser in PARSERS]
