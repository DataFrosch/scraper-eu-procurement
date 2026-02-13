"""
Tests for scraper.py logic.
"""

import pytest
import tempfile
import tarfile
from datetime import date
from pathlib import Path
from unittest.mock import Mock, patch
from decimal import Decimal

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from tedawards.scraper import (
    download_package,
    get_package_files,
    save_document,
    get_session,
    get_downloaded_packages,
    get_package_number,
    download_year,
    import_year,
)
from tedawards.models import (
    Base,
    TEDDocument,
    ContractingBody,
    Contract,
    Award,
    Contractor,
    CpvCode,
    ProcedureType,
    award_contractors,
    contract_cpv_codes,
)
from tedawards.schema import (
    TedAwardDataModel,
    DocumentModel,
    ContractingBodyModel,
    ContractModel,
    CpvCodeEntry,
    ProcedureTypeEntry,
    AwardModel,
    ContractorModel,
)

TEST_DATABASE_URL = "postgresql://tedawards:tedawards@localhost:5433/tedawards_test"


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_db():
    """Create a PostgreSQL test database with fresh tables for each test."""
    engine = create_engine(TEST_DATABASE_URL, echo=False)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

    with (
        patch("tedawards.scraper.engine", engine),
        patch("tedawards.scraper.SessionLocal", SessionLocal),
    ):
        yield engine

    engine.dispose()


@pytest.fixture
def sample_award_data():
    """Create sample award data for testing."""
    return TedAwardDataModel(
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


class TestDownloadPackage:
    """Tests for download_package function."""

    def test_existing_files_skipped(self, temp_data_dir):
        """Test that existing files are skipped without download."""
        package_number = 202400001
        extract_dir = temp_data_dir / "202400001"
        extract_dir.mkdir()

        # Create existing XML files
        xml_file = extract_dir / "test.xml"
        xml_file.write_text("<test/>")

        with patch("requests.get") as mock_get:
            result = download_package(package_number, temp_data_dir)

            # Should not make HTTP request
            mock_get.assert_not_called()
            assert result is True

    def test_download_and_extract_tar_gz(self, temp_data_dir):
        """Test downloading and extracting tar.gz archive."""
        package_number = 202400001

        # Create a mock tar.gz archive with actual content
        tar_path = temp_data_dir / "test.tar.gz"
        with tarfile.open(tar_path, "w:gz") as tar:
            # Create a temporary XML file to add
            xml_file = temp_data_dir / "temp_test.xml"
            xml_file.write_text("<test/>")
            tar.add(xml_file, arcname="test.xml")
            xml_file.unlink()

        tar_data = tar_path.read_bytes()
        tar_path.unlink()

        # Mock HTTP response
        mock_response = Mock()
        mock_response.content = tar_data
        mock_response.raise_for_status = Mock()

        with patch("requests.get", return_value=mock_response):
            result = download_package(package_number, temp_data_dir)

            assert result is True

            # Verify files were extracted
            files = get_package_files(package_number, temp_data_dir)
            assert len(files) == 1
            assert files[0].name == "test.xml"

            # Archive should be cleaned up
            archive_path = temp_data_dir / "202400001.tar.gz"
            assert not archive_path.exists()

    def test_404_returns_false(self, temp_data_dir):
        """Test that 404 returns False."""
        package_number = 202400001

        import requests

        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.HTTPError(
            response=mock_response
        )

        with patch("requests.get", return_value=mock_response):
            result = download_package(package_number, temp_data_dir)
            assert result is False

    def test_http_error_raises_exception(self, temp_data_dir):
        """Test that non-404 HTTP errors are properly raised."""
        package_number = 202400001

        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("500 Server Error")

        with patch("requests.get", return_value=mock_response):
            with pytest.raises(Exception, match="500 Server Error"):
                download_package(package_number, temp_data_dir)


class TestGetPackageFiles:
    """Tests for get_package_files function."""

    def test_returns_files_from_package(self, temp_data_dir):
        """Test that files are returned from package directory."""
        package_number = 202400001
        extract_dir = temp_data_dir / "202400001"
        extract_dir.mkdir()

        xml_file = extract_dir / "test.xml"
        xml_file.write_text("<test/>")

        files = get_package_files(package_number, temp_data_dir)
        assert len(files) == 1
        assert files[0] == xml_file

    def test_returns_none_if_not_downloaded(self, temp_data_dir):
        """Test that None is returned if package not downloaded."""
        files = get_package_files(202400001, temp_data_dir)
        assert files is None

    def test_returns_none_if_directory_empty(self, temp_data_dir):
        """Test that None is returned if directory exists but is empty."""
        package_number = 202400001
        extract_dir = temp_data_dir / "202400001"
        extract_dir.mkdir()

        files = get_package_files(package_number, temp_data_dir)
        assert files is None

    def test_case_insensitive_file_detection(self, temp_data_dir):
        """Test that uppercase extensions are also detected."""
        package_number = 202400001
        extract_dir = temp_data_dir / "202400001"
        extract_dir.mkdir()

        xml_file = extract_dir / "test.XML"
        zip_file = extract_dir / "test.ZIP"
        xml_file.write_text("<test/>")
        zip_file.write_bytes(b"PK")

        files = get_package_files(package_number, temp_data_dir)
        assert len(files) == 2
        assert xml_file in files
        assert zip_file in files


class TestSaveDocument:
    """Tests for save_document function."""

    def test_save_single_award(self, test_db, sample_award_data):
        """Test saving a single award to database."""
        from tedawards.scraper import SessionLocal

        assert save_document(sample_award_data) is True

        session = SessionLocal()
        try:
            doc = session.execute(
                select(TEDDocument).where(TEDDocument.doc_id == "12345-2024")
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
                select(Contract).where(Contract.ted_doc_id == "12345-2024")
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
        from tedawards.scraper import SessionLocal

        assert save_document(sample_award_data) is True
        assert save_document(sample_award_data) is False

        session = SessionLocal()
        try:
            docs = session.execute(
                select(TEDDocument).where(TEDDocument.doc_id == "12345-2024")
            ).all()
            assert len(docs) == 1
        finally:
            session.close()

    def test_save_same_contractor_deduplicated(self, test_db):
        """Test that same contractor in different documents creates one shared record."""
        from tedawards.scraper import SessionLocal

        award_data_1 = TedAwardDataModel(
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

        award_data_2 = TedAwardDataModel(
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
        from tedawards.scraper import SessionLocal

        award_data = TedAwardDataModel(
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
        from tedawards.scraper import SessionLocal

        assert save_document(sample_award_data) is True
        assert save_document(sample_award_data) is False

        session = SessionLocal()
        try:
            assert len(session.execute(select(TEDDocument)).all()) == 1
            assert len(session.execute(select(ContractingBody)).all()) == 1
            assert len(session.execute(select(Contract)).all()) == 1
            assert len(session.execute(select(Award)).all()) == 1
            assert len(session.execute(select(Contractor)).all()) == 1
        finally:
            session.close()

    def test_contracting_body_deduplicated(self, test_db):
        """Test that identical contracting bodies across documents are deduplicated."""
        from tedawards.scraper import SessionLocal

        award_data_1 = TedAwardDataModel(
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

        award_data_2 = TedAwardDataModel(
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
            assert len(session.execute(select(TEDDocument)).all()) == 2

            # Only one contracting body row (deduplicated)
            cbs = session.execute(select(ContractingBody)).all()
            assert len(cbs) == 1

            # Both documents point to the same contracting body
            doc1 = session.execute(
                select(TEDDocument).where(TEDDocument.doc_id == "12345-2024")
            ).scalar_one()
            doc2 = session.execute(
                select(TEDDocument).where(TEDDocument.doc_id == "67890-2024")
            ).scalar_one()
            assert doc1.contracting_body_id == doc2.contracting_body_id

            assert len(session.execute(select(Contract)).all()) == 2
        finally:
            session.close()

    def test_different_contracting_bodies_not_deduplicated(self, test_db):
        """Test that contracting bodies with different fields remain separate."""
        from tedawards.scraper import SessionLocal

        award_data_1 = TedAwardDataModel(
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

        award_data_2 = TedAwardDataModel(
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
        from tedawards.scraper import SessionLocal

        award_data_1 = TedAwardDataModel(
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

        award_data_2 = TedAwardDataModel(
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
        from tedawards.scraper import SessionLocal

        # First doc has description
        award_data_1 = TedAwardDataModel(
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
        award_data_2 = TedAwardDataModel(
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
        from tedawards.scraper import SessionLocal

        award_data_1 = TedAwardDataModel(
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
                    code="1", description="Open procedure"
                ),
            ),
            awards=[AwardModel(contractors=[])],
        )

        award_data_2 = TedAwardDataModel(
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
                    code="1", description="Open procedure"
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
            assert pt_rows[0][0].code == "1"
            assert pt_rows[0][0].description == "Open procedure"

            # Both contracts reference the same procedure type
            contracts = session.execute(select(Contract)).all()
            assert len(contracts) == 2
            for row in contracts:
                assert row[0].procedure_type_code == "1"
        finally:
            session.close()

    def test_procedure_type_description_preserved_when_null(self, test_db):
        """Test that existing description is preserved when later doc has NULL description."""
        from tedawards.scraper import SessionLocal

        award_data_1 = TedAwardDataModel(
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
        award_data_2 = TedAwardDataModel(
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
        from tedawards.scraper import SessionLocal

        award_data = TedAwardDataModel(
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
        from tedawards.scraper import SessionLocal

        # Need to create a contracting body first for the FK
        cb_session = SessionLocal()
        cb = ContractingBody(official_name="Test CB")
        cb_session.add(cb)
        cb_session.commit()
        cb_id = cb.id
        cb_session.close()

        with get_session() as session:
            doc = TEDDocument(
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
                select(TEDDocument).where(TEDDocument.doc_id == "test-doc")
            ).scalar_one_or_none()
            assert result is not None
        finally:
            verify_session.close()

    def test_session_rolls_back_on_exception(self, test_db):
        """Test that session rolls back when exception occurs."""
        from tedawards.scraper import SessionLocal

        cb_session = SessionLocal()
        cb = ContractingBody(official_name="Test CB")
        cb_session.add(cb)
        cb_session.commit()
        cb_id = cb.id
        cb_session.close()

        with pytest.raises(ValueError):
            with get_session() as session:
                doc = TEDDocument(
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
                select(TEDDocument).where(TEDDocument.doc_id == "test-doc")
            ).scalar_one_or_none()
            assert result is None
        finally:
            verify_session.close()


class TestGetPackageNumber:
    """Tests for get_package_number function."""

    def test_first_issue_of_year(self):
        """Test calculation for first issue of year."""
        assert get_package_number(2024, 1) == 202400001

    def test_last_issue_of_year(self):
        """Test calculation for a high issue number."""
        assert get_package_number(2024, 253) == 202400253

    def test_different_years(self):
        """Test that different years produce different package numbers."""
        assert get_package_number(2023, 100) == 202300100
        assert get_package_number(2024, 100) == 202400100
        assert get_package_number(2023, 100) != get_package_number(2024, 100)


class TestDownloadPackageResumeBehavior:
    """Tests for download_package resume behavior."""

    def test_uses_existing_extracted_data(self, temp_data_dir):
        """Test that existing extracted data is reused without re-download."""
        package_number = 202400001
        extract_dir = temp_data_dir / "202400001"
        extract_dir.mkdir()

        # Create existing XML files
        xml_file = extract_dir / "test.xml"
        xml_file.write_text("<test/>")

        with patch("requests.get") as mock_get:
            result = download_package(package_number, temp_data_dir)

            # Should NOT make HTTP request
            mock_get.assert_not_called()
            assert result is True

    def test_downloads_if_directory_missing(self, temp_data_dir):
        """Test that package is downloaded if directory doesn't exist."""
        package_number = 202400001

        # Create mock tar.gz archive
        tar_path = temp_data_dir / "test.tar.gz"
        with tarfile.open(tar_path, "w:gz") as tar:
            xml_file = temp_data_dir / "temp.xml"
            xml_file.write_text("<test/>")
            tar.add(xml_file, arcname="test.xml")
            xml_file.unlink()

        tar_data = tar_path.read_bytes()
        tar_path.unlink()

        mock_response = Mock()
        mock_response.content = tar_data
        mock_response.raise_for_status = Mock()

        with patch("requests.get", return_value=mock_response):
            result = download_package(package_number, temp_data_dir)

            assert result is True
            files = get_package_files(package_number, temp_data_dir)
            assert len(files) == 1
            assert files[0].name == "test.xml"

    def test_downloads_if_directory_empty(self, temp_data_dir):
        """Test that package is downloaded if directory exists but is empty."""
        package_number = 202400001
        extract_dir = temp_data_dir / "202400001"
        extract_dir.mkdir()
        # Directory exists but has no files

        # Create mock tar.gz archive
        tar_path = temp_data_dir / "test.tar.gz"
        with tarfile.open(tar_path, "w:gz") as tar:
            xml_file = temp_data_dir / "temp.xml"
            xml_file.write_text("<test/>")
            tar.add(xml_file, arcname="test.xml")
            xml_file.unlink()

        tar_data = tar_path.read_bytes()
        tar_path.unlink()

        mock_response = Mock()
        mock_response.content = tar_data
        mock_response.raise_for_status = Mock()

        with patch("requests.get", return_value=mock_response):
            result = download_package(package_number, temp_data_dir)

            # Should download since directory was empty
            assert result is True
            files = get_package_files(package_number, temp_data_dir)
            assert len(files) == 1


class TestDownloadYear:
    """Tests for download_year function."""

    def test_starts_from_issue_1(self, temp_data_dir):
        """Test that download always starts from issue 1."""
        requested_issues = []

        def mock_download(package_num, data_dir):
            issue = package_num % 100000
            requested_issues.append(issue)
            return False

        with patch("tedawards.scraper.download_package", side_effect=mock_download):
            download_year(2024, max_issue=20, data_dir=temp_data_dir)

        assert requested_issues[0] == 1


class TestGetDownloadedPackages:
    """Tests for get_downloaded_packages function."""

    def test_no_packages(self, temp_data_dir):
        """Test when no packages exist."""
        packages = get_downloaded_packages(2024, temp_data_dir)
        assert packages == []

    def test_returns_sorted_packages(self, temp_data_dir):
        """Test that packages are returned sorted."""
        (temp_data_dir / "202400010").mkdir()
        (temp_data_dir / "202400005").mkdir()
        (temp_data_dir / "202400015").mkdir()

        packages = get_downloaded_packages(2024, temp_data_dir)
        assert packages == [202400005, 202400010, 202400015]

    def test_filters_by_year(self, temp_data_dir):
        """Test that only packages for requested year are returned."""
        (temp_data_dir / "202300010").mkdir()
        (temp_data_dir / "202400005").mkdir()
        (temp_data_dir / "202500001").mkdir()

        packages = get_downloaded_packages(2024, temp_data_dir)
        assert packages == [202400005]


class TestImportYear:
    """Tests for import_year function."""

    def test_imports_all_downloaded_packages(self, test_db, temp_data_dir):
        """Test that import_year processes all downloaded packages."""
        # Create package directories with files
        for issue in [1, 2, 3]:
            pkg_dir = temp_data_dir / f"20240000{issue}"
            pkg_dir.mkdir()
            (pkg_dir / "test.xml").write_text("<test/>")

        imported_packages = []

        def mock_import(package_num, data_dir, executor=None):
            imported_packages.append(package_num)
            return 0

        with patch("tedawards.scraper.import_package", side_effect=mock_import):
            import_year(2024, temp_data_dir)

        assert imported_packages == [202400001, 202400002, 202400003]
