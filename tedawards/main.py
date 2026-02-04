import click
import logging
import os
from datetime import datetime
from .scraper import download_year, import_year

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(levelname)s - %(message)s",
)


@click.group()
def cli():
    """TED Awards scraper for EU procurement contract awards."""
    pass


@cli.command()
@click.option("--year", type=int, help="Single year to download")
@click.option("--start-year", type=int, help="Start year for range")
@click.option("--end-year", type=int, help="End year for range (default: current year)")
def download(year, start_year, end_year):
    """Download TED packages without importing to database.

    Skips packages that are already downloaded.
    Use --year for a single year, or --start-year/--end-year for a range.
    """
    if year and start_year:
        raise click.UsageError("Use either --year or --start-year/--end-year, not both")
    if not year and not start_year:
        raise click.UsageError("Must specify --year or --start-year")

    if year:
        download_year(year)
    else:
        if end_year is None:
            end_year = datetime.now().year
        for y in range(start_year, end_year + 1):
            download_year(y)


@cli.command(name="import")
@click.option("--year", type=int, help="Single year to import")
@click.option("--start-year", type=int, help="Start year for range")
@click.option("--end-year", type=int, help="End year for range (default: current year)")
def import_cmd(year, start_year, end_year):
    """Import downloaded TED packages into the database.

    Use --year for a single year, or --start-year/--end-year for a range.
    """
    if year and start_year:
        raise click.UsageError("Use either --year or --start-year/--end-year, not both")
    if not year and not start_year:
        raise click.UsageError("Must specify --year or --start-year")

    if year:
        import_year(year)
    else:
        if end_year is None:
            end_year = datetime.now().year
        for y in range(start_year, end_year + 1):
            import_year(y)


if __name__ == "__main__":
    cli()
