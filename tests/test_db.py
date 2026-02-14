"""
Tests for db.py — shared database logic.
"""

import pytest
from datetime import date
from unittest.mock import patch
from decimal import Decimal

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker

from awards.db import (
    save_document,
    get_session,
    _normalize_country_code,
)
from awards.models import (
    Base,
    Document,
    ContractingBody,
    Contract,
    Award,
    Contractor,
    CpvCode,
    Country,
    ProcedureType,
    award_contractors,
    contract_cpv_codes,
)
from awards.schema import (
    AwardDataModel,
    DocumentModel,
    ContractingBodyModel,
    ContractModel,
    CpvCodeEntry,
    ProcedureTypeEntry,
    AwardModel,
    ContractorModel,
)

TEST_DATABASE_URL = "postgresql://awards:awards@localhost:5433/awards_test"


@pytest.fixture
def test_db():
    """Create a PostgreSQL test database with fresh tables for each test."""
    engine = create_engine(TEST_DATABASE_URL, echo=False)
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.commit()
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

    with (
        patch("awards.db.engine", engine),
        patch("awards.db.SessionLocal", SessionLocal),
    ):
        yield engine

    engine.dispose()


@pytest.fixture
def sample_award_data():
    """Create sample award data for testing."""
    return AwardDataModel(
        document=DocumentModel(
            doc_id="12345-2024",
            edition="2024/S 001-000001",
            publication_date=date(2024, 1, 1),
            source_country="DE",
        ),
        contracting_body=ContractingBodyModel(
            official_name="Test Contracting Body",
            town="Berlin",
            country_code="DE",
            nuts_code="DE300",
        ),
        contract=ContractModel(
            title="Test Contract",
            main_cpv_code="45000000",
            cpv_codes=[CpvCodeEntry(code="45000000")],
            nuts_code="DE212",
        ),
        awards=[
            AwardModel(
                award_title="Award 1",
                awarded_value=50000.0,
                awarded_value_currency="EUR",
                tenders_received=5,
                contractors=[
                    ContractorModel(
                        official_name="Test Contractor GmbH",
                        town="Munich",
                        country_code="DE",
                        nuts_code="DE212",
                    )
                ],
            )
        ],
    )


class TestSaveDocument:
    """Tests for save_document function."""

    def test_save_single_award(self, test_db, sample_award_data):
        """Test saving a single award to database."""
        from awards.db import SessionLocal

        assert save_document(sample_award_data) is True

        session = SessionLocal()
        try:
            doc = session.execute(
                select(Document).where(Document.doc_id == "12345-2024")
            ).scalar_one()
            assert doc.edition == "2024/S 001-000001"
            assert doc.contracting_body_id is not None

            cb = session.execute(
                select(ContractingBody).where(
                    ContractingBody.official_name == "Test Contracting Body"
                )
            ).scalar_one()
            assert doc.contracting_body_id == cb.id
            assert cb.nuts_code == "DE300"

            contract = session.execute(
                select(Contract).where(Contract.doc_id == "12345-2024")
            ).scalar_one()
            assert contract.title == "Test Contract"
            assert contract.nuts_code == "DE212"

            award = session.execute(
                select(Award).where(Award.contract_id == contract.id)
            ).scalar_one()
            assert award.awarded_value == Decimal("50000.00")
            assert award.tenders_received == 5

            contractor = session.execute(
                select(Contractor).where(
                    Contractor.official_name == "Test Contractor GmbH"
                )
            ).scalar_one()
            assert contractor.country_code == "DE"
            assert contractor.nuts_code == "DE212"

            # Verify junction table link
            link = session.execute(
                select(award_contractors).where(
                    award_contractors.c.award_id == award.id,
                    award_contractors.c.contractor_id == contractor.id,
                )
            ).one()
            assert link is not None
        finally:
            session.close()

    def test_save_duplicate_document_skipped(self, test_db, sample_award_data):
        """Test that duplicate documents are skipped (idempotent import)."""
        from awards.db import SessionLocal

        assert save_document(sample_award_data) is True
        assert save_document(sample_award_data) is False

        session = SessionLocal()
        try:
            docs = session.execute(
                select(Document).where(Document.doc_id == "12345-2024")
            ).all()
            assert len(docs) == 1
        finally:
            session.close()

    def test_save_same_contractor_deduplicated(self, test_db):
        """Test that same contractor in different documents creates one shared record."""
        from awards.db import SessionLocal

        award_data_1 = AwardDataModel(
            document=DocumentModel(
                doc_id="12345-2024",
                edition="2024/S 001-000001",
                publication_date=date(2024, 1, 1),
                source_country="DE",
            ),
            contracting_body=ContractingBodyModel(
                official_name="Test Body 1", country_code="DE"
            ),
            contract=ContractModel(title="Contract 1"),
            awards=[
                AwardModel(
                    contractors=[
                        ContractorModel(
                            official_name="Shared Contractor Ltd", country_code="GB"
                        )
                    ]
                )
            ],
        )

        award_data_2 = AwardDataModel(
            document=DocumentModel(
                doc_id="67890-2024",
                edition="2024/S 001-000002",
                publication_date=date(2024, 1, 2),
                source_country="FR",
            ),
            contracting_body=ContractingBodyModel(
                official_name="Test Body 2", country_code="FR"
            ),
            contract=ContractModel(title="Contract 2"),
            awards=[
                AwardModel(
                    contractors=[
                        ContractorModel(
                            official_name="Shared Contractor Ltd", country_code="GB"
                        )
                    ]
                )
            ],
        )

        save_document(award_data_1)
        save_document(award_data_2)

        session = SessionLocal()
        try:
            # Only one contractor row (deduplicated)
            contractors = session.execute(
                select(Contractor).where(
                    Contractor.official_name == "Shared Contractor Ltd"
                )
            ).all()
            assert len(contractors) == 1

            # But two junction table rows (one per award)
            links = session.execute(select(award_contractors)).all()
            assert len(links) == 2
        finally:
            session.close()

    def test_save_multiple_awards_same_contract(self, test_db):
        """Test saving multiple awards for same contract."""
        from awards.db import SessionLocal

        award_data = AwardDataModel(
            document=DocumentModel(
                doc_id="12345-2024",
                edition="2024/S 001-000001",
                publication_date=date(2024, 1, 1),
                source_country="DE",
            ),
            contracting_body=ContractingBodyModel(
                official_name="Test Body", country_code="DE"
            ),
            contract=ContractModel(title="Multi-lot Contract"),
            awards=[
                AwardModel(
                    award_title="Lot 1",
                    awarded_value=10000.0,
                    awarded_value_currency="EUR",
                    contractors=[
                        ContractorModel(official_name="Contractor A", country_code="DE")
                    ],
                ),
                AwardModel(
                    award_title="Lot 2",
                    awarded_value=20000.0,
                    awarded_value_currency="EUR",
                    contractors=[
                        ContractorModel(official_name="Contractor B", country_code="FR")
                    ],
                ),
            ],
        )

        assert save_document(award_data) is True

        session = SessionLocal()
        try:
            awards = session.execute(select(Award)).all()
            assert len(awards) == 2

            contractors = session.execute(select(Contractor)).all()
            assert len(contractors) == 2

            links = session.execute(select(award_contractors)).all()
            assert len(links) == 2
        finally:
            session.close()

    def test_save_reimport_is_idempotent(self, test_db, sample_award_data):
        """Test that re-importing the same data is idempotent (skips existing docs)."""
        from awards.db import SessionLocal

        assert save_document(sample_award_data) is True
        assert save_document(sample_award_data) is False

        session = SessionLocal()
        try:
            assert len(session.execute(select(Document)).all()) == 1
            assert len(session.execute(select(ContractingBody)).all()) == 1
            assert len(session.execute(select(Contract)).all()) == 1
            assert len(session.execute(select(Award)).all()) == 1
            assert len(session.execute(select(Contractor)).all()) == 1
        finally:
            session.close()

    def test_contracting_body_deduplicated(self, test_db):
        """Test that identical contracting bodies across documents are deduplicated."""
        from awards.db import SessionLocal

        award_data_1 = AwardDataModel(
            document=DocumentModel(
                doc_id="12345-2024",
                publication_date=date(2024, 1, 1),
                source_country="DE",
            ),
            contracting_body=ContractingBodyModel(
                official_name="Ministry of Health", country_code="DE", town="Berlin"
            ),
            contract=ContractModel(title="Medical Supplies Contract 2024"),
            awards=[AwardModel(contractors=[])],
        )

        award_data_2 = AwardDataModel(
            document=DocumentModel(
                doc_id="67890-2024",
                publication_date=date(2024, 1, 15),
                source_country="DE",
            ),
            contracting_body=ContractingBodyModel(
                official_name="Ministry of Health", country_code="DE", town="Berlin"
            ),
            contract=ContractModel(title="IT Services Contract 2024"),
            awards=[AwardModel(contractors=[])],
        )

        save_document(award_data_1)
        save_document(award_data_2)

        session = SessionLocal()
        try:
            assert len(session.execute(select(Document)).all()) == 2

            # Only one contracting body row (deduplicated)
            cbs = session.execute(select(ContractingBody)).all()
            assert len(cbs) == 1

            # Both documents point to the same contracting body
            doc1 = session.execute(
                select(Document).where(Document.doc_id == "12345-2024")
            ).scalar_one()
            doc2 = session.execute(
                select(Document).where(Document.doc_id == "67890-2024")
            ).scalar_one()
            assert doc1.contracting_body_id == doc2.contracting_body_id

            assert len(session.execute(select(Contract)).all()) == 2
        finally:
            session.close()

    def test_different_contracting_bodies_not_deduplicated(self, test_db):
        """Test that contracting bodies with different fields remain separate."""
        from awards.db import SessionLocal

        award_data_1 = AwardDataModel(
            document=DocumentModel(
                doc_id="12345-2024",
                publication_date=date(2024, 1, 1),
                source_country="DE",
            ),
            contracting_body=ContractingBodyModel(
                official_name="Ministry of Health", country_code="DE", town="Berlin"
            ),
            contract=ContractModel(title="Contract 1"),
            awards=[AwardModel(contractors=[])],
        )

        award_data_2 = AwardDataModel(
            document=DocumentModel(
                doc_id="67890-2024",
                publication_date=date(2024, 1, 15),
                source_country="FR",
            ),
            contracting_body=ContractingBodyModel(
                official_name="Ministry of Health", country_code="FR", town="Paris"
            ),
            contract=ContractModel(title="Contract 2"),
            awards=[AwardModel(contractors=[])],
        )

        save_document(award_data_1)
        save_document(award_data_2)

        session = SessionLocal()
        try:
            cbs = session.execute(select(ContractingBody)).all()
            assert len(cbs) == 2
        finally:
            session.close()

    def test_cpv_code_lookup_table_deduplication(self, test_db):
        """Test that same CPV code from two documents creates one lookup row."""
        from awards.db import SessionLocal

        award_data_1 = AwardDataModel(
            document=DocumentModel(
                doc_id="12345-2024",
                publication_date=date(2024, 1, 1),
                source_country="DE",
            ),
            contracting_body=ContractingBodyModel(
                official_name="Body 1", country_code="DE"
            ),
            contract=ContractModel(
                title="Contract 1",
                main_cpv_code="45000000",
                cpv_codes=[
                    CpvCodeEntry(
                        code="45000000",
                        description="Construction work",
                    )
                ],
            ),
            awards=[AwardModel(contractors=[])],
        )

        award_data_2 = AwardDataModel(
            document=DocumentModel(
                doc_id="67890-2024",
                publication_date=date(2024, 1, 2),
                source_country="FR",
            ),
            contracting_body=ContractingBodyModel(
                official_name="Body 2", country_code="FR"
            ),
            contract=ContractModel(
                title="Contract 2",
                main_cpv_code="45000000",
                cpv_codes=[
                    CpvCodeEntry(
                        code="45000000",
                        description="Construction work",
                    )
                ],
            ),
            awards=[AwardModel(contractors=[])],
        )

        save_document(award_data_1)
        save_document(award_data_2)

        session = SessionLocal()
        try:
            # Only one CPV code row (deduplicated)
            cpv_rows = session.execute(select(CpvCode)).all()
            assert len(cpv_rows) == 1
            assert cpv_rows[0][0].code == "45000000"
            assert cpv_rows[0][0].description == "Construction work"

            # But two junction table rows (one per contract)
            links = session.execute(select(contract_cpv_codes)).all()
            assert len(links) == 2
        finally:
            session.close()

    def test_cpv_description_preserved_when_null(self, test_db):
        """Test that existing description is preserved when later doc has NULL description."""
        from awards.db import SessionLocal

        # First doc has description
        award_data_1 = AwardDataModel(
            document=DocumentModel(
                doc_id="12345-2024",
                publication_date=date(2024, 1, 1),
                source_country="DE",
            ),
            contracting_body=ContractingBodyModel(
                official_name="Body 1", country_code="DE"
            ),
            contract=ContractModel(
                title="Contract 1",
                main_cpv_code="45000000",
                cpv_codes=[
                    CpvCodeEntry(
                        code="45000000",
                        description="Construction work",
                    )
                ],
            ),
            awards=[AwardModel(contractors=[])],
        )

        # Second doc has NULL description (e.g. eForms)
        award_data_2 = AwardDataModel(
            document=DocumentModel(
                doc_id="67890-2024",
                publication_date=date(2024, 1, 2),
                source_country="FR",
            ),
            contracting_body=ContractingBodyModel(
                official_name="Body 2", country_code="FR"
            ),
            contract=ContractModel(
                title="Contract 2",
                main_cpv_code="45000000",
                cpv_codes=[CpvCodeEntry(code="45000000", description=None)],
            ),
            awards=[AwardModel(contractors=[])],
        )

        save_document(award_data_1)
        save_document(award_data_2)

        session = SessionLocal()
        try:
            cpv = session.execute(
                select(CpvCode).where(CpvCode.code == "45000000")
            ).scalar_one()
            assert cpv.description == "Construction work", (
                "Description should be preserved when later doc has NULL"
            )
        finally:
            session.close()

    def test_procedure_type_lookup_table_deduplication(self, test_db):
        """Test that same procedure type from two documents creates one lookup row."""
        from awards.db import SessionLocal

        award_data_1 = AwardDataModel(
            document=DocumentModel(
                doc_id="12345-2024",
                publication_date=date(2024, 1, 1),
                source_country="DE",
            ),
            contracting_body=ContractingBodyModel(
                official_name="Body 1", country_code="DE"
            ),
            contract=ContractModel(
                title="Contract 1",
                procedure_type=ProcedureTypeEntry(
                    code="open", description="Open procedure"
                ),
            ),
            awards=[AwardModel(contractors=[])],
        )

        award_data_2 = AwardDataModel(
            document=DocumentModel(
                doc_id="67890-2024",
                publication_date=date(2024, 1, 2),
                source_country="FR",
            ),
            contracting_body=ContractingBodyModel(
                official_name="Body 2", country_code="FR"
            ),
            contract=ContractModel(
                title="Contract 2",
                procedure_type=ProcedureTypeEntry(
                    code="open", description="Open procedure"
                ),
            ),
            awards=[AwardModel(contractors=[])],
        )

        save_document(award_data_1)
        save_document(award_data_2)

        session = SessionLocal()
        try:
            # Only one procedure type row (deduplicated)
            pt_rows = session.execute(select(ProcedureType)).all()
            assert len(pt_rows) == 1
            assert pt_rows[0][0].code == "open"
            assert pt_rows[0][0].description == "Open procedure"

            # Both contracts reference the same procedure type
            contracts = session.execute(select(Contract)).all()
            assert len(contracts) == 2
            for row in contracts:
                assert row[0].procedure_type_code == "open"
        finally:
            session.close()

    def test_procedure_type_description_preserved_when_null(self, test_db):
        """Test that existing description is preserved when later doc has NULL description."""
        from awards.db import SessionLocal

        award_data_1 = AwardDataModel(
            document=DocumentModel(
                doc_id="12345-2024",
                publication_date=date(2024, 1, 1),
                source_country="DE",
            ),
            contracting_body=ContractingBodyModel(
                official_name="Body 1", country_code="DE"
            ),
            contract=ContractModel(
                title="Contract 1",
                procedure_type=ProcedureTypeEntry(
                    code="open", description="Open procedure"
                ),
            ),
            awards=[AwardModel(contractors=[])],
        )

        # Second doc has NULL description (e.g. eForms)
        award_data_2 = AwardDataModel(
            document=DocumentModel(
                doc_id="67890-2024",
                publication_date=date(2024, 1, 2),
                source_country="FR",
            ),
            contracting_body=ContractingBodyModel(
                official_name="Body 2", country_code="FR"
            ),
            contract=ContractModel(
                title="Contract 2",
                procedure_type=ProcedureTypeEntry(code="open", description=None),
            ),
            awards=[AwardModel(contractors=[])],
        )

        save_document(award_data_1)
        save_document(award_data_2)

        session = SessionLocal()
        try:
            pt = session.execute(
                select(ProcedureType).where(ProcedureType.code == "open")
            ).scalar_one()
            assert pt.description == "Open procedure", (
                "Description should be preserved when later doc has NULL"
            )
        finally:
            session.close()

    def test_duplicate_cpv_code_deduplicated(self, test_db):
        """Test that duplicate CPV codes in list create one junction table row."""
        from awards.db import SessionLocal

        award_data = AwardDataModel(
            document=DocumentModel(
                doc_id="12345-2024",
                publication_date=date(2024, 1, 1),
                source_country="DE",
            ),
            contracting_body=ContractingBodyModel(
                official_name="Body 1", country_code="DE"
            ),
            contract=ContractModel(
                title="Contract 1",
                main_cpv_code="50750000",
                cpv_codes=[
                    CpvCodeEntry(code="50750000"),
                    CpvCodeEntry(code="50750000"),
                ],
            ),
            awards=[AwardModel(contractors=[])],
        )

        save_document(award_data)

        session = SessionLocal()
        try:
            links = session.execute(select(contract_cpv_codes)).all()
            assert len(links) == 1
        finally:
            session.close()


class TestGetSession:
    """Tests for get_session context manager."""

    def test_session_commits_on_success(self, test_db):
        """Test that session commits when no exception occurs."""
        from awards.db import SessionLocal

        # Need to create a contracting body first for the FK
        cb_session = SessionLocal()
        cb = ContractingBody(official_name="Test CB")
        cb_session.add(cb)
        cb_session.commit()
        cb_id = cb.id
        cb_session.close()

        with get_session() as session:
            doc = Document(
                doc_id="test-doc",
                edition="2024/S 001-000001",
                publication_date=date(2024, 1, 1),
                contracting_body_id=cb_id,
            )
            session.add(doc)

        # Verify document was committed
        verify_session = SessionLocal()
        try:
            result = verify_session.execute(
                select(Document).where(Document.doc_id == "test-doc")
            ).scalar_one_or_none()
            assert result is not None
        finally:
            verify_session.close()

    def test_session_rolls_back_on_exception(self, test_db):
        """Test that session rolls back when exception occurs."""
        from awards.db import SessionLocal

        cb_session = SessionLocal()
        cb = ContractingBody(official_name="Test CB")
        cb_session.add(cb)
        cb_session.commit()
        cb_id = cb.id
        cb_session.close()

        with pytest.raises(ValueError):
            with get_session() as session:
                doc = Document(
                    doc_id="test-doc",
                    edition="2024/S 001-000001",
                    publication_date=date(2024, 1, 1),
                    contracting_body_id=cb_id,
                )
                session.add(doc)
                raise ValueError("Test error")

        # Verify document was NOT committed
        verify_session = SessionLocal()
        try:
            result = verify_session.execute(
                select(Document).where(Document.doc_id == "test-doc")
            ).scalar_one_or_none()
            assert result is None
        finally:
            verify_session.close()


class TestNormalizeCountryCode:
    """Tests for _normalize_country_code function."""

    def test_uk_maps_to_gb(self):
        assert _normalize_country_code("UK") == "GB"

    def test_uk_lowercase_maps_to_gb(self):
        assert _normalize_country_code("uk") == "GB"

    def test_1a_maps_to_none(self):
        assert _normalize_country_code("1A") is None

    def test_empty_string_maps_to_none(self):
        assert _normalize_country_code("") is None

    def test_none_maps_to_none(self):
        assert _normalize_country_code(None) is None

    def test_normal_code_uppercased(self):
        assert _normalize_country_code("de") == "DE"

    def test_normal_code_preserved(self):
        assert _normalize_country_code("FR") == "FR"


class TestCountryLookupTable:
    """Tests for country lookup table integration."""

    def test_country_deduplication(self, test_db):
        """Two docs with same country code -> one countries row."""
        from awards.db import SessionLocal

        award_data_1 = AwardDataModel(
            document=DocumentModel(
                doc_id="12345-2024",
                publication_date=date(2024, 1, 1),
                source_country="DE",
            ),
            contracting_body=ContractingBodyModel(
                official_name="Body 1", country_code="DE"
            ),
            contract=ContractModel(title="Contract 1"),
            awards=[AwardModel(contractors=[])],
        )

        award_data_2 = AwardDataModel(
            document=DocumentModel(
                doc_id="67890-2024",
                publication_date=date(2024, 1, 2),
                source_country="DE",
            ),
            contracting_body=ContractingBodyModel(
                official_name="Body 2", country_code="DE"
            ),
            contract=ContractModel(title="Contract 2"),
            awards=[AwardModel(contractors=[])],
        )

        save_document(award_data_1)
        save_document(award_data_2)

        session = SessionLocal()
        try:
            de_rows = session.execute(select(Country).where(Country.code == "DE")).all()
            assert len(de_rows) == 1
            assert de_rows[0][0].name == "Germany"
        finally:
            session.close()

    def test_country_name_preserved(self, test_db):
        """Country name is preserved when a later doc doesn't provide one (COALESCE)."""
        from awards.db import SessionLocal

        # First doc creates country with name from pycountry
        award_data_1 = AwardDataModel(
            document=DocumentModel(
                doc_id="12345-2024",
                publication_date=date(2024, 1, 1),
                source_country="FR",
            ),
            contracting_body=ContractingBodyModel(
                official_name="Body 1", country_code="FR"
            ),
            contract=ContractModel(title="Contract 1"),
            awards=[AwardModel(contractors=[])],
        )

        # Second doc also references FR
        award_data_2 = AwardDataModel(
            document=DocumentModel(
                doc_id="67890-2024",
                publication_date=date(2024, 1, 2),
                source_country="FR",
            ),
            contracting_body=ContractingBodyModel(
                official_name="Body 2", country_code="FR"
            ),
            contract=ContractModel(title="Contract 2"),
            awards=[AwardModel(contractors=[])],
        )

        save_document(award_data_1)
        save_document(award_data_2)

        session = SessionLocal()
        try:
            fr = session.execute(
                select(Country).where(Country.code == "FR")
            ).scalar_one()
            assert fr.name == "France"
        finally:
            session.close()

    def test_uk_normalized_to_gb_in_country_table(self, test_db):
        """UK country code is normalized to GB and stored in countries table."""
        from awards.db import SessionLocal

        award_data = AwardDataModel(
            document=DocumentModel(
                doc_id="12345-2024",
                publication_date=date(2024, 1, 1),
                source_country="UK",
            ),
            contracting_body=ContractingBodyModel(
                official_name="Body 1", country_code="UK"
            ),
            contract=ContractModel(title="Contract 1"),
            awards=[
                AwardModel(
                    contractors=[
                        ContractorModel(official_name="UK Ltd", country_code="UK")
                    ]
                )
            ],
        )

        save_document(award_data)

        session = SessionLocal()
        try:
            # GB row exists with correct name
            gb = session.execute(
                select(Country).where(Country.code == "GB")
            ).scalar_one()
            assert "United Kingdom" in gb.name

            # No UK row
            uk = session.execute(
                select(Country).where(Country.code == "UK")
            ).scalar_one_or_none()
            assert uk is None

            # All entities stored as GB
            doc = session.execute(
                select(Document).where(Document.doc_id == "12345-2024")
            ).scalar_one()
            assert doc.source_country == "GB"

            cb = session.execute(select(ContractingBody)).scalar_one()
            assert cb.country_code == "GB"

            ct = session.execute(select(Contractor)).scalar_one()
            assert ct.country_code == "GB"
        finally:
            session.close()

    def test_contractor_country_upserted(self, test_db):
        """Country from contractor is upserted into countries table."""
        from awards.db import SessionLocal

        award_data = AwardDataModel(
            document=DocumentModel(
                doc_id="12345-2024",
                publication_date=date(2024, 1, 1),
                source_country="DE",
            ),
            contracting_body=ContractingBodyModel(
                official_name="Body 1", country_code="DE"
            ),
            contract=ContractModel(title="Contract 1"),
            awards=[
                AwardModel(
                    contractors=[
                        ContractorModel(official_name="Polish Co", country_code="PL")
                    ]
                )
            ],
        )

        save_document(award_data)

        session = SessionLocal()
        try:
            countries = {row[0].code for row in session.execute(select(Country)).all()}
            assert "DE" in countries
            assert "PL" in countries
        finally:
            session.close()
