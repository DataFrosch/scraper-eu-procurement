"""
TED XML parsers for various format versions.

Each parser module provides:
- can_parse(file_path: Path) -> bool
- get_format_name() -> str
- parse_xml_file(file_path: Path) -> Optional[List[TedAwardDataModel]]
"""

from . import ted_v2, ted_meta_xml, ted_internal_ojs, eforms_ubl
from .factory import get_parser, parse_file, get_supported_formats

__all__ = [
    # Parser modules
    "ted_v2",
    "ted_meta_xml",
    "ted_internal_ojs",
    "eforms_ubl",
    # Factory functions
    "get_parser",
    "parse_file",
    "get_supported_formats",
]
