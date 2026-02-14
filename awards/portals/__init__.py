"""Portal modules for procurement data sources."""

from typing import Protocol

from .ted import TEDPortal


class Portal(Protocol):
    """Interface that each portal module must implement."""

    name: str

    def download(self, start_year: int, end_year: int) -> None: ...

    def import_data(self, start_year: int, end_year: int) -> None: ...


PORTALS: dict[str, Portal] = {
    "ted": TEDPortal(),
}
