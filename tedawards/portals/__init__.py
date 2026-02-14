"""Portal modules for procurement data sources."""

from typing import Protocol


class Portal(Protocol):
    """Interface that each portal module must implement."""

    name: str

    def download(self, start_year: int, end_year: int) -> None: ...

    def import_data(self, start_year: int, end_year: int) -> None: ...


PORTALS: dict[str, Portal] = {}


def register(portal: Portal) -> None:
    PORTALS[portal.name] = portal
