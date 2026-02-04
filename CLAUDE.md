# TED Awards Scraper - Claude Context

## Project Overview

TED Awards scraper for analyzing EU procurement contract awards from **2011 onwards**. Processes XML-formatted TED data, focusing **only on award notices** (document type 7 - "Contract award notice").

## Tech Stack & Requirements

- **Development**: uv for dependency management
- **Database**: PostgreSQL 18 via Docker Compose, SQLAlchemy ORM
- **Python**: >=3.12 with lxml, requests, sqlalchemy, psycopg2-binary, pydantic, click

## Key Architecture Decisions

1. **Award-only focus**: Filter XML parsing to only process contract award notices
2. **Environment configuration**: All DB settings via env vars (.env for dev)
3. **Year-based scraping**: Scrape by year, iterating through sequential OJ issue numbers (not calendar dates)
4. **Raw source data model**: Store data exactly as it appears in each TED document. No deduplication at import time - each document has its own contracting body and contractor records. Deduplication can be done later as a separate layer (views, entity resolution) on top of the raw data.
5. **Pydantic as parser contract**: Pydantic models in `schema.py` define the interface between parsers and the database layer. This enables:
   - Fast parser tests without database setup (just validate Pydantic output)
   - Runtime type validation catches parser bugs early
   - Clear contract that all parsers must conform to
   - Parallel development of parsers (each targeting same Pydantic schema)
6. **No fallbacks or defaults**: Only extract data directly from XML files - no defaults, no fallbacks, no default records. Missing data should be None in Python and NULL in database. If we cannot extract required data, skip the record entirely rather than creating defaults
7. **Fail-loud error handling**: Errors should always bubble up and cause loud failures. Never silently ignore errors or continue processing with partial data. Use proper exception handling but let errors propagate to calling code for proper error reporting and debugging. This includes:
   - **Never assume defaults**: If required data is missing, raise an exception rather than assuming a default value
   - **Never gracefully degrade**: If data integrity cannot be guaranteed, fail immediately rather than producing potentially incorrect results
   - **Always validate critical assumptions**: If business logic depends on certain data being present, validate it exists and fail if it doesn't
8. **Explicit data extraction**: Use built-in Python and standard library methods - no custom utility wrappers. Every assumption about data format must be explicit and testable:
   - **Prefer standard library**: Use built-in methods over custom implementations (e.g., Python's date parsing, lxml's text extraction)
   - **Explicit errors**: When parsing fails, error messages must show the actual data value that failed, not just generic messages
   - **Data quality first**: Code should reveal data quality issues, not paper over them with fallbacks
9. **Strict format-specific parsing**: Each XML format has well-defined value structures - use direct parsing without generic wrappers:
   - **R2.0.7/R2.0.8**: VALUE_COST elements have `FMTVAL` attribute with clean numeric value (e.g., `FMTVAL="19979964.32"`)
   - **R2.0.9**: VAL_TOTAL elements have clean decimal text (e.g., `2850000.00`)
   - **No fallbacks**: If expected attribute/format is missing, fail loudly

## Data Source Details

- **URL Pattern**: `https://ted.europa.eu/packages/daily/{yyyynnnnn}` where `nnnnn` is the Official Journal (OJ S) issue number (e.g., 202400001 = issue 1 of 2024)
- **Package Numbering**: Sequential issue numbers, NOT calendar days. Issues increment by 1 but skip weekends/holidays (e.g., typical year has ~250 issues)
- **File Format**: `.tar.gz` archives containing XML documents
- **Coverage**: XML data from **January 2011 onwards** (earlier 2008-2010 data uses different formats not supported)
- **Rate Limits**: 3 concurrent downloads, 700 requests/min, 600 downloads per 6min/IP
- **Scraping Strategy**: Try sequential issue numbers starting from 1, stopping after 10 consecutive 404s

### Supported XML Formats

The scraper supports two TED XML document formats:

1. **TED 2.0 XML (2011-2024)** - **Unified Parser**

   - **Variants**:
     - **R2.0.7 (2011-2013)**: XML with CONTRACT_AWARD forms, VALUE_COST with FMTVAL attribute
     - **R2.0.8 (2014-2015)**: XML with CONTRACT_AWARD forms, VALUE_COST with FMTVAL attribute
     - **R2.0.9 (2014-2024)**: XML with F03_2014 forms, VAL_TOTAL with clean decimal text
   - **Format**: XML with TED_EXPORT namespace
   - **File naming**: `{6-8digits}_{year}.xml` (e.g., 000248_2012.xml)
   - **Parser**: `TedV2Parser` - unified parser handling all TED 2.0 variants with automatic format detection
   - **First available**: 2011-01-04
   - **Language handling**: Daily archives contain **one XML file per document** in its **original language**
     - Each document includes:
       - `FORM_SECTION` with form in original language (e.g., `<F03_2014 LG="DE">`)
       - `CODED_DATA_SECTION` with English descriptions for CPV codes, NUTS, etc.
     - **Parser processes ALL documents regardless of original language**
     - Titles and organization names are stored in the original submission language
     - `TRANSLATION_SECTION` exists but is ignored (only contains translated titles, not form data)
     - **CRITICAL**: Do NOT filter by language - would lose 95%+ of documents

2. **eForms UBL ContractAwardNotice (2025+)**
   - **Format**: UBL-based XML with ContractAwardNotice schema
   - **Namespace**: `urn:oasis:names:specification:ubl:schema:xsd:ContractAwardNotice-2`
   - **Parser**: `EFormsUBLParser` - handles new EU eForms standard
   - **Language handling**: One file per document, text fields in original submission language
     - **Parser processes ALL documents regardless of language**

## Database Architecture

Database setup handled directly in `scraper.py`:

- Engine and session factory created at module level from environment variables
- `get_session()` context manager for transaction management with automatic commit/rollback
- Schema automatically created on scraper initialization

SQLAlchemy models in `models.py` (raw source data, no deduplication):

- `ted_documents` - Main document metadata (PK: doc_id)
- `contracting_bodies` - Purchasing organizations (one per document, FK to ted_documents)
- `contracts` - Procurement items (FK to ted_documents and contracting_bodies)
- `awards` - Award decisions (FK to contracts)
- `contractors` - Winning companies (one per award, FK to awards)

Relationships are 1:many throughout - each document has its own records. Re-importing the same document is idempotent (skipped if doc_id exists).

## Format Detection & Parser Selection

The `ParserFactory` automatically detects and selects the appropriate parser:

- **Priority Order**: TedV2Parser → EFormsUBLParser
- **Detection**: Each parser has a `can_parse()` method to identify compatible formats
- **File Types**: Handles `.xml` files
- **TED 2.0 Auto-Detection**: The unified TedV2Parser automatically detects R2.0.7, R2.0.8, or R2.0.9 variants

### Archive Structure

- **TED 2.0 (2011+)**: `.tar.gz` containing individual `.xml` files with TED_EXPORT namespace

## Key XML Data Structures

### TED 2.0 R2.0.9 (F03_2014 Award Notice)

- `TED_EXPORT/CODED_DATA_SECTION` - Document metadata
- `TED_EXPORT/FORM_SECTION/F03_2014` - Award notice data
  - `CONTRACTING_BODY` - Buyer info
  - `OBJECT_CONTRACT` - Contract details with `VAL_TOTAL` (clean decimal text)
  - `AWARD_CONTRACT` - Winner and value info

### TED 2.0 R2.0.7/R2.0.8 (CONTRACT_AWARD)

- `TED_EXPORT/CODED_DATA_SECTION` - Document metadata
- `TED_EXPORT/FORM_SECTION/CONTRACT_AWARD` - Award notice data
  - `VALUE_COST` elements with `FMTVAL` attribute containing numeric value

## Development Commands

```bash
# Download packages for a single year (skips already downloaded)
uv run tedawards download --start-year 2024

# Download packages for a range of years
uv run tedawards download --start-year 2011 --end-year 2024

# Import downloaded packages for a single year
uv run tedawards import --start-year 2024

# Import downloaded packages for a range of years
uv run tedawards import --start-year 2011 --end-year 2024
```

## Code Organization

- `scraper.py` - Main scraper with database setup and session management
- `models.py` - SQLAlchemy ORM models (raw source data, no deduplication)
- `schema.py` - Pydantic models defining the parser output contract (enables fast parser testing without DB)
- `parsers/` - Format-specific XML parsers (each must return valid Pydantic models)
- `main.py` - CLI interface

## Environment Variables

- `DATABASE_URL` - PostgreSQL connection string (default: `postgresql://tedawards:tedawards@localhost:5432/tedawards`)
- `TED_DATA_DIR` - Local storage for downloaded archives (default: `./data`)
- `LOG_LEVEL` - Logging configuration (default: `INFO`)
