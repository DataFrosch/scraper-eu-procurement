import logging
import os
import requests
import tarfile
from pathlib import Path
from typing import List, Optional
from contextlib import contextmanager
from dotenv import load_dotenv
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session

from .parsers import try_parse_award
from .models import Base, TEDDocument, ContractingBody, Contract, Award, Contractor
from .schema import TedAwardDataModel

load_dotenv()

logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://tedawards:tedawards@localhost:5432/tedawards"
)

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

# Data directory setup
DATA_DIR = Path(os.getenv("TED_DATA_DIR", "./data"))
DATA_DIR.mkdir(exist_ok=True)


@contextmanager
def get_session() -> Session:
    """Get database session as context manager."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_package_number(year: int, issue: int) -> int:
    """Calculate TED package number from year and OJ issue number."""
    return year * 100000 + issue


def download_package(package_number: int, data_dir: Path = DATA_DIR) -> bool:
    """Download and extract a single daily package.

    Args:
        package_number: TED package number (yyyynnnnn format)
        data_dir: Directory to store downloaded data

    Returns:
        True if downloaded successfully, False if package doesn't exist (404)
    """
    package_url = f"https://ted.europa.eu/packages/daily/{package_number:09d}"
    package_str = f"{package_number:09d}"
    archive_path = data_dir / f"{package_str}.tar.gz"
    extract_dir = data_dir / package_str

    # Skip if already downloaded and extracted
    if extract_dir.exists():
        existing_files = [f for f in extract_dir.glob("**/*") if f.is_file()]
        if existing_files:
            logger.info(f"Package {package_str}: already downloaded")
            return True

    # Download package
    logger.info(f"Package {package_str}: downloading")
    try:
        response = requests.get(package_url, timeout=30)
        response.raise_for_status()
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            logger.info(f"Package {package_str}: not found")
            return False
        logger.error(f"Failed to download package {package_str}: {e}")
        raise
    except requests.RequestException as e:
        logger.error(f"Failed to download package {package_str}: {e}")
        raise

    # Save and extract
    archive_path.write_bytes(response.content)
    logger.debug(f"Downloaded {len(response.content)} bytes for package {package_str}")

    extract_dir.mkdir(exist_ok=True)
    try:
        with tarfile.open(archive_path, "r:gz") as tar_file:
            tar_file.extractall(extract_dir, filter="data")
    except tarfile.TarError as e:
        logger.error(f"Failed to extract package {package_str}: {e}")
        raise

    # Clean up archive file
    archive_path.unlink()

    return True


def get_package_files(
    package_number: int, data_dir: Path = DATA_DIR
) -> Optional[List[Path]]:
    """Get list of files from an already-downloaded package.

    Args:
        package_number: TED package number (yyyynnnnn format)
        data_dir: Directory where packages are stored

    Returns:
        List of file paths, or None if package not downloaded
    """
    package_str = f"{package_number:09d}"
    extract_dir = data_dir / package_str

    if not extract_dir.exists():
        return None

    files = [f for f in extract_dir.glob("**/*") if f.is_file()]
    return files if files else None


def save_document(award_data: TedAwardDataModel) -> bool:
    """Save a single award document to database in its own transaction.

    Returns True if saved, False if already exists.
    """
    doc_id = award_data.document.doc_id

    with get_session() as session:
        existing = session.execute(
            select(TEDDocument.doc_id).where(TEDDocument.doc_id == doc_id)
        ).scalar_one_or_none()
        if existing:
            logger.debug(f"Document {doc_id} already imported, skipping")
            return False

        doc = TEDDocument(**award_data.document.model_dump())

        cb = ContractingBody(**award_data.contracting_body.model_dump())
        doc.contracting_bodies.append(cb)

        contract = Contract(**award_data.contract.model_dump())
        contract.document = doc
        contract.contracting_body = cb

        for award_item in award_data.awards:
            award_dict = award_item.model_dump()
            contractors_data = award_dict.pop("contractors", [])

            award = Award(**award_dict)
            contract.awards.append(award)

            for contractor_data in contractors_data:
                award.contractors.append(Contractor(**contractor_data))

        session.add(doc)
        return True


def download_year(year: int, max_issue: int = 300, data_dir: Path = DATA_DIR):
    """Download TED packages for a year.

    Args:
        year: The year to download
        max_issue: Maximum issue number to try (default: 300)
        data_dir: Directory for storing downloaded packages
    """
    logger.info(
        f"Downloading TED packages for year {year} (issues 1-{max_issue}, stopping after 10 consecutive 404s)"
    )

    total_downloaded = 0
    consecutive_404s = 0
    max_consecutive_404s = 10

    for issue in range(1, max_issue + 1):
        package_number = get_package_number(year, issue)
        success = download_package(package_number, data_dir)

        if not success:
            consecutive_404s += 1
            if consecutive_404s >= max_consecutive_404s:
                logger.info(
                    f"Stopping after {max_consecutive_404s} consecutive 404s at issue {issue}"
                )
                break
            continue

        consecutive_404s = 0
        total_downloaded += 1

    logger.info(f"Year {year}: Downloaded {total_downloaded} packages")


def get_downloaded_packages(year: int, data_dir: Path = DATA_DIR) -> List[int]:
    """Get list of downloaded package numbers for a year.

    Args:
        year: Year to check
        data_dir: Directory where packages are stored

    Returns:
        Sorted list of package numbers that have been downloaded
    """
    year_prefix = str(year)
    packages = []

    for item in data_dir.iterdir():
        if item.is_dir() and item.name.startswith(year_prefix) and len(item.name) == 9:
            try:
                package_num = int(item.name)
                pkg_year = package_num // 100000
                if pkg_year == year:
                    packages.append(package_num)
            except ValueError:
                continue

    return sorted(packages)


def import_package(package_number: int, data_dir: Path = DATA_DIR) -> int:
    """Import awards from a single downloaded package.

    Each document is saved in its own transaction, so successfully imported
    documents are preserved even if a later document fails.

    Args:
        package_number: TED package number (yyyynnnnn format)
        data_dir: Directory where packages are stored

    Returns:
        Number of award notices imported
    """
    files = get_package_files(package_number, data_dir)
    if files is None:
        logger.warning(f"Package {package_number:09d} not found in {data_dir}")
        return 0

    xml_files = [f for f in files if f.suffix.lower() == ".xml"]

    count = 0
    for file_path in xml_files:
        awards = try_parse_award(file_path)
        if not awards:
            continue
        for award_data in awards:
            if save_document(award_data):
                count += 1

    if count:
        logger.info(f"Package {package_number:09d}: Imported {count} award notices")
    return count


def import_year(year: int, data_dir: Path = DATA_DIR):
    """Import awards from all downloaded packages for a year.

    Args:
        year: The year to import
        data_dir: Directory where packages are stored
    """
    Base.metadata.create_all(engine)

    packages = get_downloaded_packages(year, data_dir)
    if not packages:
        logger.warning(f"No downloaded packages found for year {year}")
        return

    logger.info(f"Importing {len(packages)} packages for year {year}")

    total_imported = 0
    for package_number in packages:
        total_imported += import_package(package_number, data_dir)

    logger.info(f"Year {year}: Imported {total_imported} total award notices")
