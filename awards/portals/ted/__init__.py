"""TED Europa portal — download and import EU-wide procurement data."""

from .portal import (  # noqa: F401
    TEDPortal,
    try_parse_award,
    download_package,
    download_year,
    get_downloaded_packages,
    get_package_files,
    get_package_number,
    import_package,
    import_year,
)

__all__ = [
    "TEDPortal",
    "try_parse_award",
    "download_package",
    "download_year",
    "get_downloaded_packages",
    "get_package_files",
    "get_package_number",
    "import_package",
    "import_year",
]
