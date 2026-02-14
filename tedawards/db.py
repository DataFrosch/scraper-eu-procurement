import logging
import os
from contextlib import contextmanager
from dotenv import load_dotenv
from sqlalchemy import bindparam, create_engine, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import sessionmaker, Session

from sqlalchemy import text as sa_text

from .countries import get_country_name
from .models import (
    Document,
    ContractingBody,
    Contract,
    Award,
    Contractor,
    CpvCode,
    ProcedureType,
    AuthorityType,
    Country,
    award_contractors,
    contract_cpv_codes,
)
from .schema import AwardDataModel

load_dotenv()

logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://tedawards:tedawards@localhost:5432/tedawards"
)

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

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

_country_ins = pg_insert(Country.__table__)
_upsert_country = _country_ins.on_conflict_do_update(
    index_elements=["code"],
    set_={"name": func.coalesce(_country_ins.excluded.name, Country.__table__.c.name)},
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
_insert_doc = Document.__table__.insert()
_insert_contract = Contract.__table__.insert().returning(Contract.__table__.c.id)
_insert_award = Award.__table__.insert().returning(Award.__table__.c.id)
_insert_cpv_junc = contract_cpv_codes.insert()
_insert_award_ct = award_contractors.insert()

# Doc existence check
_check_doc = select(Document.__table__.c.doc_id).where(
    Document.__table__.c.doc_id == bindparam("doc_id")
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


def _normalize_country_code(value: str | None) -> str | None:
    if not value:
        return None
    code = value.upper()
    if code == "UK":
        return "GB"
    if code == "1A":
        return None
    return code


def _save_document_core(session: Session, award_data: AwardDataModel) -> bool:
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

    # Normalize country codes
    cb_dict["country_code"] = _normalize_country_code(cb_dict.get("country_code"))
    doc_params = award_data.document.model_dump()
    doc_params["source_country"] = _normalize_country_code(
        doc_params.get("source_country")
    )

    # Collect all contractor country codes (normalized) for batch upsert
    all_contractor_dicts = []
    for award_item in award_data.awards:
        for c in award_item.contractors:
            cd = c.model_dump()
            cd["country_code"] = _normalize_country_code(cd.get("country_code"))
            all_contractor_dicts.append(cd)

    # Upsert all distinct country codes before entities (FK dependency)
    country_codes = {
        code
        for code in [
            cb_dict["country_code"],
            doc_params["source_country"],
            *(cd["country_code"] for cd in all_contractor_dicts),
        ]
        if code is not None
    }
    if country_codes:
        session.execute(
            _upsert_country,
            [{"code": c, "name": get_country_name(c)} for c in country_codes],
        )

    # Upsert contracting body
    cb_id = session.execute(_upsert_cb, cb_dict).scalar_one()

    # Create document with FK to contracting body
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
    contract_dict["doc_id"] = doc_id
    contract_id = session.execute(_insert_contract, contract_dict).scalar_one()

    # Link all CPV codes to contract
    cpv_junc_params = [
        {"contract_id": contract_id, "cpv_code": code}
        for code in {e["code"] for e in cpv_codes_data}
    ]
    if cpv_junc_params:
        session.execute(_insert_cpv_junc, cpv_junc_params)

    # Create awards with contractor upserts (using pre-normalized dicts)
    all_award_ct_params = []
    ct_offset = 0
    for award_item in award_data.awards:
        award_dict = award_item.model_dump()
        contractors_raw = award_dict.pop("contractors", [])

        award_dict["contract_id"] = contract_id
        award_id = session.execute(_insert_award, award_dict).scalar_one()

        # Slice pre-normalized contractor dicts for this award
        contractors_data = all_contractor_dicts[
            ct_offset : ct_offset + len(contractors_raw)
        ]
        ct_offset += len(contractors_raw)

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


def save_document(award_data: AwardDataModel) -> bool:
    """Save a single award document to database in its own transaction.

    Returns True if saved, False if already exists.
    """
    with get_session() as session:
        return _save_document_core(session, award_data)


_MATERIALIZED_VIEW_SQL = """\
CREATE MATERIALIZED VIEW IF NOT EXISTS awards_adjusted AS
SELECT
    a.id AS award_id, a.contract_id, c.doc_id,
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
JOIN documents d ON c.doc_id = d.doc_id
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
