# Awards Scraper - Claude Context

## Project Overview

Scraper for analyzing EU procurement contract awards from **2011 onwards**. Processes XML-formatted procurement data, focusing **only on award notices** (document type 7 - "Contract award notice").

## Tech Stack & Requirements

- **Development**: uv for dependency management, pre-commit hooks with Ruff (linting + formatting)
- **Database**: PostgreSQL 18 via Docker Compose, SQLAlchemy ORM
- **Python**: >=3.12 with lxml, requests, sqlalchemy, psycopg2-binary, python-dotenv, pydantic, click

## Key Architecture Decisions

1. **Award-only focus**: Filter XML parsing to only process contract award notices
2. **Environment configuration**: All DB settings via env vars (.env for dev, loaded via python-dotenv)
3. **Year-based scraping**: Scrape by year, iterating through sequential OJ issue numbers (not calendar dates)
4. **Raw source data with exact-match entity deduplication**: Store data as-is from TED documents. All organizations (buyers and contractors) go into a single shared `organizations` lookup table where only exact duplicates are merged (all 6 address fields must match). Fuzzy matching, outlier filtering, and entity resolution belong in a separate analysis layer.
5. **Pydantic as parser contract**: Pydantic models in `schema.py` define the interface between parsers and the database layer.
6. **Fail-loud, no defaults, no fallbacks**: Only extract data directly from XML — missing data is `None`/`NULL`, never a default value. Errors bubble up loudly with the actual bad data value in the message. Code should reveal data quality issues, not paper over them.
7. **Strict monetary parsing**: `parsers/monetary.py` has dedicated parsers for each locale-specific format. Formats are mutually exclusive — if multiple parsers match, it raises an error. Unparseable values log a warning and return None.
8. **SQLAlchemy Core for bulk imports**: Module-level prepared Core statements (`pg_insert` with `on_conflict_do_update`) for all upserts, avoiding ORM overhead. Entire packages imported in a single transaction.

## Data Source Details

- **URL Pattern**: `https://ted.europa.eu/packages/daily/{yyyynnnnn}` where `nnnnn` is the OJ S issue number (e.g., 202400001 = issue 1 of 2024)
- **Package Numbering**: Sequential issue numbers, NOT calendar days. Skip weekends/holidays (~250 issues/year)
- **File Format**: `.tar.gz` archives containing XML documents
- **Coverage**: XML data from **January 2011 onwards** (earlier data uses unsupported formats)
- **Rate Limits**: 3 concurrent downloads, 700 requests/min, 600 downloads per 6min/IP
- **Scraping Strategy**: Try sequential issue numbers starting from 1, stop after 10 consecutive 404s

### Supported XML Formats

1. **TED 2.0 XML (2011-2024)** — `portals/ted/ted_v2.parse_xml_file()`
   - R2.0.7 (2011-2013) and R2.0.8 (2014-2015): CONTRACT_AWARD forms, VALUE_COST elements
   - R2.0.9 (2014-2024): F03_2014 forms, VAL_TOTAL elements
   - Variant auto-detected within the parser

2. **eForms UBL ContractAwardNotice (2025+)** — `portals/ted/eforms_ubl.parse_xml_file()`

**CRITICAL**: Do NOT filter by language — archives contain one XML per document in its original language. Filtering would lose 95%+ of documents.

### Code Normalization

Coded values (procedure types, authority types, contract nature codes) use exact eForms codes (lowercase, hyphens). TED v2 codes are mapped forward to eForms equivalents following the official [OP-TED/ted-xml-data-converter](https://github.com/OP-TED/ted-xml-data-converter) mappings (`xslt/other-mappings.xml`). In eForms, "accelerated" is a separate boolean (BT-106), not a procedure type variant — the `contracts.accelerated` column captures this.

## Database Architecture

Schema in `models.py`, setup in `db.py`.

**Tables:** `documents` (PK: `doc_id`), `contracts`, `awards`, `organizations` (unified buyers+contractors), `cpv_codes` (natural key: `code`), `procedure_types` (natural key: `code`), `authority_types` (natural key: `code`), `organization_identifiers`

**Junction tables:** `award_contractors` (award_id, organization_id), `contract_cpv_codes`

**Key relationships:** `documents.buyer_organization_id` → `organizations.id`; `documents.buyer_authority_type_code` → `authority_types.code`; `documents.buyer_main_activity_code` stores the buyer's role per-notice (not on the org, since it's per-notice context).

Deduplication uses PostgreSQL upsert-returning (`INSERT ... ON CONFLICT DO UPDATE ... RETURNING id`). Re-importing the same document is idempotent (skipped if doc_id exists).

## Code Organization

- `main.py` - CLI interface (click commands: `download`, `import`, `update-rates`; `--portal` flag)
- `db.py` - Database setup, SQLAlchemy Core statements, session management, materialized view
- `models.py` - SQLAlchemy ORM models
- `schema.py` - Pydantic models (parser output contract)
- `portals/` - Per-source download/import logic
  - `__init__.py` - Explicit PORTALS dict with portal instances
  - `ted/` - TED Europa portal package
    - `__init__.py` - `try_parse_award()` entry point with format detection, re-exports
    - `portal.py` - Download/import logic and `TEDPortal` class
    - `ted_v2.py` - Unified TED 2.0 parser (all variants)
    - `eforms_ubl.py` - eForms UBL parser
- `parsers/` - Shared parsing utilities
  - `monetary.py` - Monetary value parsing (11 format-specific parsers)
  - `xml.py` - XML extraction helpers (`elem_text`, `elem_attr`, `first_text`, `first_attr`, `element_text`, `xpath_text`)

## Development Commands

```bash
# Download/import packages (all portals)
uv run awards download --start-year 2024
uv run awards download --start-year 2011 --end-year 2024
uv run awards import --start-year 2024
uv run awards import --start-year 2011 --end-year 2024

# Limit to specific portal(s)
uv run awards download --start-year 2024 --portal ted
uv run awards import --start-year 2024 --portal ted

# Docker services
docker compose up -d                      # Main database (port 5432)
docker compose --profile test up -d       # Test database (port 5433)
docker compose --profile analytics up -d  # Metabase (port 3000)

# Database dump/restore
make dump
make restore FILE=dumps/awards_YYYYMMDD_HHMMSS.dump

# Tests (requires test database running)
uv run pytest tests/ -v
```

## Environment Variables

- `DATABASE_URL` - PostgreSQL connection string (default: `postgresql://awards:awards@localhost:5432/awards`)
- `TED_DATA_DIR` - Local storage for downloaded archives (default: `./data`)
- `LOG_LEVEL` - Logging configuration (default: `INFO`)
