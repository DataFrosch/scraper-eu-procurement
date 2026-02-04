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
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from .parsers import ParserFactory
from .models import Base, TEDDocument, ContractingBody, Contract, Award, Contractor
from .schema import TedAwardDataModel, TedParserResultModel

load_dotenv()

logger = logging.getLogger(__name__)

# Database setup
DB_PATH = Path(os.getenv('DB_PATH', './tedawards.db'))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    echo=False,
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

# Data directory setup
DATA_DIR = Path(os.getenv('TED_DATA_DIR', './data'))
DATA_DIR.mkdir(exist_ok=True)

# Parser factory (module-level singleton)
parser_factory = ParserFactory()


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
        existing_files = [f for f in extract_dir.glob('**/*') if f.is_file()]
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
            logger.debug(f"Package not available (404): {package_str}")
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
        with tarfile.open(archive_path, 'r:gz') as tar_file:
            tar_file.extractall(extract_dir, filter='data')
    except tarfile.TarError as e:
        logger.error(f"Failed to extract package {package_str}: {e}")
        raise

    # Clean up archive file
    archive_path.unlink()

    return True


def get_package_files(package_number: int, data_dir: Path = DATA_DIR) -> Optional[List[Path]]:
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

    files = [f for f in extract_dir.glob('**/*') if f.is_file()]
    return files if files else None


def process_file(file_path: Path) -> TedParserResultModel:
    """Process a single file (XML or ZIP) and return parser result."""
    try:
        # Get appropriate parser for this file
        parser = parser_factory.get_parser(file_path)
        if not parser:
            logger.debug(f"No parser available for {file_path.name}")
            return None

        # Parse file - returns TedParserResultModel
        result = parser.parse_xml_file(file_path)
        if not result:
            logger.debug(f"Failed to parse {file_path.name} with {parser.get_format_name()}")
            return None

        logger.debug(f"Parsed {file_path.name} using {parser.get_format_name()}, found {len(result.awards)} award documents")
        return result

    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        raise


def save_awards(session: Session, awards: List[TedAwardDataModel]) -> int:
    """Save award data to database with proper deduplication using RETURNING."""
    count = 0
    insert_func = sqlite_insert if engine.dialect.name == 'sqlite' else pg_insert

    for award_data in awards:
        try:
            # Insert/update document with RETURNING to get doc_id
            doc_values = award_data.document.model_dump()
            stmt = insert_func(TEDDocument).values(**doc_values)
            stmt = stmt.on_conflict_do_update(
                index_elements=['doc_id'],
                set_={'doc_id': stmt.excluded.doc_id}  # No-op update to trigger RETURNING
            ).returning(TEDDocument.doc_id)
            doc_id = session.execute(stmt).scalar_one()

            # Insert/update contracting body with RETURNING to get id
            cb_data = award_data.contracting_body.model_dump()
            cb_hash = award_data.contracting_body.entity_hash
            cb_data['entity_hash'] = cb_hash

            stmt = insert_func(ContractingBody).values(**cb_data)
            stmt = stmt.on_conflict_do_update(
                index_elements=['entity_hash'],
                set_={'entity_hash': stmt.excluded.entity_hash}  # No-op update
            ).returning(ContractingBody.id)
            cb_id = session.execute(stmt).scalar_one()

            # Insert document-contracting body relationship with INSERT OR IGNORE
            from .models import document_contracting_bodies
            stmt = insert_func(document_contracting_bodies).values(
                ted_doc_id=doc_id,
                contracting_body_id=cb_id
            )
            stmt = stmt.on_conflict_do_nothing()
            session.execute(stmt)

            # Insert/update contract with RETURNING to get id
            contract_data = award_data.contract.model_dump()
            contract_data['ted_doc_id'] = doc_id
            contract_data['contracting_body_id'] = cb_id
            contract_data.pop('performance_nuts_code', None)

            stmt = insert_func(Contract).values(**contract_data)
            stmt = stmt.on_conflict_do_update(
                index_elements=['ted_doc_id', 'title'],
                set_={'ted_doc_id': stmt.excluded.ted_doc_id}  # No-op update
            ).returning(Contract.id)
            contract_id = session.execute(stmt).scalar_one()

            # Insert awards and contractors
            for award_item in award_data.awards:
                award_dict = award_item.model_dump()
                contractors_data = award_dict.pop('contractors', [])
                award_dict['contract_id'] = contract_id

                # Insert/update award with RETURNING to get id
                stmt = insert_func(Award).values(**award_dict)
                stmt = stmt.on_conflict_do_update(
                    index_elements=['contract_id', 'award_title', 'conclusion_date'],
                    set_={'contract_id': stmt.excluded.contract_id}  # No-op update
                ).returning(Award.id)
                award_id = session.execute(stmt).scalar_one()

                # Insert contractors and link to awards
                for contractor_item in award_item.contractors:
                    contractor_data = contractor_item.model_dump()
                    contractor_hash = contractor_item.entity_hash
                    contractor_data['entity_hash'] = contractor_hash

                    stmt = insert_func(Contractor).values(**contractor_data)
                    stmt = stmt.on_conflict_do_update(
                        index_elements=['entity_hash'],
                        set_={'entity_hash': stmt.excluded.entity_hash}  # No-op update
                    ).returning(Contractor.id)
                    contractor_id = session.execute(stmt).scalar_one()

                    # Insert award-contractor relationship with INSERT OR IGNORE
                    from .models import award_contractors
                    stmt = insert_func(award_contractors).values(
                        award_id=award_id,
                        contractor_id=contractor_id
                    )
                    stmt = stmt.on_conflict_do_nothing()
                    session.execute(stmt)

            count += 1

        except Exception as e:
            logger.error(f"Error saving award {award_data.document.doc_id}: {e}")
            raise

    session.flush()
    return count


def download_year(year: int, max_issue: int = 300, data_dir: Path = DATA_DIR):
    """Download TED packages for a year.

    Args:
        year: The year to download
        max_issue: Maximum issue number to try (default: 300)
        data_dir: Directory for storing downloaded packages
    """
    logger.info(f"Downloading TED packages for year {year} (issues 1-{max_issue}, stopping after 10 consecutive 404s)")

    total_downloaded = 0
    consecutive_404s = 0
    max_consecutive_404s = 10

    for issue in range(1, max_issue + 1):
        package_number = get_package_number(year, issue)
        success = download_package(package_number, data_dir)

        if not success:
            consecutive_404s += 1
            if consecutive_404s >= max_consecutive_404s:
                logger.info(f"Stopping after {max_consecutive_404s} consecutive 404s at issue {issue}")
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

    # Filter to processable files
    processable_files = [
        f for f in files
        if (
            # TED META XML: en_*_meta_org.zip or EN_*_META_ORG.ZIP
            f.name.lower().startswith('en_') and '_meta_org.' in f.name.lower()
        ) or (
            # TED INTERNAL_OJS: *.en files
            f.suffix.lower() == '.en'
        ) or (
            # TED 2.0 and eForms: all languages in one file (*.xml)
            f.suffix.lower() == '.xml'
        )
    ]

    all_awards = []
    for file_path in processable_files:
        parser_result = process_file(file_path)
        if parser_result:
            all_awards.extend(parser_result.awards)

    if not all_awards:
        return 0

    with get_session() as session:
        saved = save_awards(session, all_awards)
        logger.info(f"Package {package_number:09d}: Imported {saved} award notices")
        return saved


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