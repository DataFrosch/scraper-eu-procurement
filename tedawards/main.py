import click
import logging
import os
from datetime import datetime
from .scraper import download_year, import_year, refresh_materialized_view
from .rates import update_rates

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(levelname)s - %(message)s",
)


@click.group()
def cli():
    """TED Awards scraper for EU procurement contract awards."""
    pass


@cli.command()
@click.option("--start-year", type=int, required=True, help="Start year")
@click.option("--end-year", type=int, help="End year (default: current year)")
def download(start_year, end_year):
    """Download TED packages without importing to database.

    Skips packages that are already downloaded.
    """
    if end_year is None:
        end_year = datetime.now().year
    for y in range(start_year, end_year + 1):
        download_year(y)


@cli.command(name="import")
@click.option("--start-year", type=int, required=True, help="Start year")
@click.option("--end-year", type=int, help="End year (default: current year)")
def import_cmd(start_year, end_year):
    """Import downloaded TED packages into the database."""
    if end_year is None:
        end_year = datetime.now().year
    for y in range(start_year, end_year + 1):
        import_year(y)
    refresh_materialized_view()


@cli.command(name="update-rates")
@click.option("--start-year", type=int, default=2011, help="Start year (default: 2011)")
@click.option("--end-year", type=int, help="End year (default: current year)")
def update_rates_cmd(start_year, end_year):
    """Fetch ECB exchange rates and Eurostat HICP data."""
    if end_year is None:
        end_year = datetime.now().year
    update_rates(start_year, end_year)
    refresh_materialized_view()


if __name__ == "__main__":
    cli()
