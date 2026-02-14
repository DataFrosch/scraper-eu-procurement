import logging
import os
import requests
import tarfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Optional
from contextlib import contextmanager
from dotenv import load_dotenv
from sqlalchemy import bindparam, create_engine, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import sessionmaker, Session

from sqlalchemy import text as sa_text

from .parsers import try_parse_award
from .models import (
    Base,
    TEDDocument,
    ContractingBody,
    Contract,
    Award,
    Contractor,
    CpvCode,
    ProcedureType,
    AuthorityType,
    award_contractors,
    contract_cpv_codes,
)
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

# --- Module-level Core statements (built once, reused with parameters) ---
# The _ins variables must exist separately because .excluded must reference
# the same pg_insert() object that on_conflict_do_update is called on.

# Lookup table upserts (no RETURNING needed)
_cpv_ins = pg_insert(CpvCode.__table__)
_upsert_cpv = _cpv_ins.on_conflict_do_update(
    index_elements=["code"],
    set_={
        "description": func.coalesce(
            _cpv_ins.excluded.description, CpvCode.__table__.c.description
        )
    },
)

_pt_ins = pg_insert(ProcedureType.__table__)
_upsert_pt = _pt_ins.on_conflict_do_update(
    index_elements=["code"],
    set_={
        "description": func.coalesce(
            _pt_ins.excluded.description, ProcedureType.__table__.c.description
        )
    },
)

_at_ins = pg_insert(AuthorityType.__table__)
_upsert_at = _at_ins.on_conflict_do_update(
    index_elements=["code"],
    set_={
        "description": func.coalesce(
            _at_ins.excluded.description, AuthorityType.__table__.c.description
        )
    },
)

# Entity table upserts (RETURNING id)
_cb_ins = pg_insert(ContractingBody.__table__)
_upsert_cb = _cb_ins.on_conflict_do_update(
    constraint="uq_contracting_body_identity",
    set_={"official_name": _cb_ins.excluded.official_name},
).returning(ContractingBody.__table__.c.id)

_ct_ins = pg_insert(Contractor.__table__)
_upsert_ct = _ct_ins.on_conflict_do_update(
    constraint="uq_contractor_identity",
    set_={"official_name": _ct_ins.excluded.official_name},
).returning(Contractor.__table__.c.id)

# Plain inserts
_insert_doc = TEDDocument.__table__.insert()
_insert_contract = Contract.__table__.insert().returning(Contract.__table__.c.id)
_insert_award = Award.__table__.insert().returning(Award.__table__.c.id)
_insert_cpv_junc = contract_cpv_codes.insert()
_insert_award_ct = award_contractors.insert()

# Doc existence check
_check_doc = select(TEDDocument.__table__.c.doc_id).where(
    TEDDocument.__table__.c.doc_id == bindparam("doc_id")
)


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


def _normalize_country_code(value: str | None) -> str | None:
    return value.upper() if value else value


def _save_document_core(session: Session, award_data: TedAwardDataModel) -> bool:
    """Save a single award document using Core statements.

    Operates within the caller's session/transaction — does not commit.
    Returns True if saved, False if already exists.
    """
    doc_id = award_data.document.doc_id

    existing = session.execute(_check_doc, {"doc_id": doc_id}).scalar_one_or_none()
    if existing:
        logger.debug(f"Document {doc_id} already imported, skipping")
        return False

    # Upsert authority type into lookup table before contracting body (FK dependency)
    cb_dict = award_data.contracting_body.model_dump()
    authority_type_data = cb_dict.pop("authority_type", None)
    if authority_type_data:
        session.execute(_upsert_at, authority_type_data)
        cb_dict["authority_type_code"] = authority_type_data["code"]

    # Upsert contracting body
    cb_dict["country_code"] = _normalize_country_code(cb_dict.get("country_code"))
    cb_id = session.execute(_upsert_cb, cb_dict).scalar_one()

    # Create document with FK to contracting body
    doc_params = award_data.document.model_dump()
    doc_params["source_country"] = _normalize_country_code(
        doc_params.get("source_country")
    )
    doc_params["contracting_body_id"] = cb_id
    session.execute(_insert_doc, doc_params)

    # Upsert CPV codes into lookup table before creating contract (FK dependency)
    contract_dict = award_data.contract.model_dump()
    cpv_codes_data = contract_dict.pop("cpv_codes", [])
    if cpv_codes_data:
        # Deduplicate by code — PG upsert can't affect the same row twice in one statement
        cpv_codes_data = list({e["code"]: e for e in cpv_codes_data}.values())
        session.execute(_upsert_cpv, cpv_codes_data)

    # Upsert procedure type into lookup table before creating contract (FK dependency)
    procedure_type_data = contract_dict.pop("procedure_type", None)
    if procedure_type_data:
        session.execute(_upsert_pt, procedure_type_data)
        contract_dict["procedure_type_code"] = procedure_type_data["code"]

    # Create contract
    contract_dict["ted_doc_id"] = doc_id
    contract_id = session.execute(_insert_contract, contract_dict).scalar_one()

    # Link all CPV codes to contract
    cpv_junc_params = [
        {"contract_id": contract_id, "cpv_code": code}
        for code in {e["code"] for e in cpv_codes_data}
    ]
    if cpv_junc_params:
        session.execute(_insert_cpv_junc, cpv_junc_params)

    # Create awards with contractor upserts
    all_award_ct_params = []
    for award_item in award_data.awards:
        award_dict = award_item.model_dump()
        contractors_data = award_dict.pop("contractors", [])

        award_dict["contract_id"] = contract_id
        award_id = session.execute(_insert_award, award_dict).scalar_one()

        for c in contractors_data:
            c["country_code"] = _normalize_country_code(c.get("country_code"))
        contractor_ids = {
            session.execute(_upsert_ct, c).scalar_one() for c in contractors_data
        }
        for contractor_id in contractor_ids:
            all_award_ct_params.append(
                {"award_id": award_id, "contractor_id": contractor_id}
            )

    if all_award_ct_params:
        session.execute(_insert_award_ct, all_award_ct_params)

    return True


def save_document(award_data: TedAwardDataModel) -> bool:
    """Save a single award document to database in its own transaction.

    Returns True if saved, False if already exists.
    """
    with get_session() as session:
        return _save_document_core(session, award_data)


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


def import_package(
    package_number: int,
    data_dir: Path = DATA_DIR,
    executor: Optional[ThreadPoolExecutor] = None,
) -> int:
    """Import awards from a single downloaded package.

    All documents are saved in a single transaction per package.
    Parsing is done in the provided thread pool executor while
    database saving runs sequentially on the calling thread.

    Args:
        package_number: TED package number (yyyynnnnn format)
        data_dir: Directory where packages are stored
        executor: Thread pool for parallel XML parsing (created if None)

    Returns:
        Number of award notices imported
    """
    files = get_package_files(package_number, data_dir)
    if files is None:
        logger.warning(f"Package {package_number:09d} not found in {data_dir}")
        return 0

    xml_files = [f for f in files if f.suffix.lower() == ".xml"]

    own_executor = executor is None
    if own_executor:
        executor = ThreadPoolExecutor()

    try:
        parsed = executor.map(try_parse_award, xml_files)

        count = 0
        with get_session() as session:
            for awards in parsed:
                if not awards:
                    continue
                for award_data in awards:
                    if _save_document_core(session, award_data):
                        count += 1
    finally:
        if own_executor:
            executor.shutdown(wait=False)

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
    with ThreadPoolExecutor() as executor:
        for package_number in packages:
            total_imported += import_package(package_number, data_dir, executor)

    logger.info(f"Year {year}: Imported {total_imported} total award notices")


_MATERIALIZED_VIEW_SQL = """\
CREATE MATERIALIZED VIEW IF NOT EXISTS awards_adjusted AS
SELECT
    a.id AS award_id, a.contract_id, c.ted_doc_id AS doc_id,
    d.publication_date, d.source_country,
    cb.official_name AS contracting_body_name,
    cb.country_code AS contracting_body_country,
    c.title AS contract_title, c.main_cpv_code,
    c.contract_nature_code, c.procedure_type_code,
    c.nuts_code AS contract_nuts_code,
    a.award_title, a.awarded_value, a.awarded_value_currency,
    a.tenders_received,
    CASE
        WHEN a.awarded_value IS NULL OR a.awarded_value_currency IS NULL THEN NULL
        WHEN a.awarded_value_currency = 'EUR' THEN a.awarded_value
        WHEN er.rate IS NOT NULL THEN ROUND(a.awarded_value / er.rate, 2)
    END AS value_eur,
    CASE
        WHEN a.awarded_value IS NULL OR a.awarded_value_currency IS NULL THEN NULL
        WHEN pi_year.index_value IS NULL OR pi_base.index_value IS NULL THEN NULL
        WHEN a.awarded_value_currency = 'EUR'
            THEN ROUND(a.awarded_value * pi_base.index_value / pi_year.index_value, 2)
        WHEN er.rate IS NOT NULL
            THEN ROUND(a.awarded_value / er.rate * pi_base.index_value / pi_year.index_value, 2)
    END AS value_eur_real
FROM awards a
JOIN contracts c ON a.contract_id = c.id
JOIN ted_documents d ON c.ted_doc_id = d.doc_id
JOIN contracting_bodies cb ON d.contracting_body_id = cb.id
LEFT JOIN exchange_rates er
    ON er.currency = a.awarded_value_currency
    AND er.year = EXTRACT(YEAR FROM d.publication_date)::int
    AND er.month = EXTRACT(MONTH FROM d.publication_date)::int
LEFT JOIN price_indices pi_year
    ON pi_year.year = EXTRACT(YEAR FROM d.publication_date)::int
LEFT JOIN (SELECT index_value FROM price_indices WHERE year = (SELECT MAX(year) FROM price_indices)) pi_base ON TRUE
WITH DATA
"""

_VIEW_INDEXES = [
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_awards_adjusted_award_id ON awards_adjusted (award_id)",
    "CREATE INDEX IF NOT EXISTS idx_awards_adjusted_pub_date ON awards_adjusted (publication_date)",
    "CREATE INDEX IF NOT EXISTS idx_awards_adjusted_country ON awards_adjusted (source_country)",
    "CREATE INDEX IF NOT EXISTS idx_awards_adjusted_cpv ON awards_adjusted (main_cpv_code)",
]


def create_materialized_view(eng=None):
    """Create the awards_adjusted materialized view if it doesn't exist."""
    eng = eng or engine
    with eng.connect() as conn:
        conn.execute(sa_text(_MATERIALIZED_VIEW_SQL))
        for idx_sql in _VIEW_INDEXES:
            conn.execute(sa_text(idx_sql))
        conn.commit()
    logger.info("Materialized view awards_adjusted ensured")


def refresh_materialized_view(eng=None):
    """Refresh the awards_adjusted materialized view concurrently."""
    eng = eng or engine
    create_materialized_view(eng)
    with eng.connect() as conn:
        conn.execute(sa_text("REFRESH MATERIALIZED VIEW CONCURRENTLY awards_adjusted"))
        conn.commit()
    logger.info("Materialized view awards_adjusted refreshed")
