# TED Awards Scraper

A Python scraper for EU procurement contract award notices from [TED Europa](https://ted.europa.eu/). Processes XML-formatted TED data from **2011 onwards**.

## Features

- Scrapes TED award notice packages by year from **January 2011 onwards** (document type 7 only)
- Supports multiple XML formats:
  - TED 2.0 R2.0.7-R2.0.9 (2011-2024) - Standard TED XML formats
  - eForms UBL (2025+) - New EU eForms standard
- SQLite database with comprehensive procurement schema (PostgreSQL also supported)
- Processes TED packages by Official Journal issue number (not calendar dates)
- Smart stopping logic: automatically detects end of year (stops after 10 consecutive 404s)
- Automatic schema creation and reference data management
- Handles duplicate data gracefully with database-level deduplication

## Quick Start

1. **Setup environment**:
   ```bash
   # Install dependencies
   uv sync
   ```

2. **Download data**:
   ```bash
   # Download packages for a year (skips already downloaded)
   uv run tedawards download --year 2024

   # Download multiple years
   uv run tedawards download --start-year 2011 --end-year 2024
   ```

3. **Import to database**:
   ```bash
   # Import downloaded packages for a year
   uv run tedawards import --year 2024

   # Import multiple years
   uv run tedawards import --start-year 2011 --end-year 2024
   ```

4. **Query data**:
   ```bash
   # SQLite database is created at ./tedawards.db by default
   sqlite3 tedawards.db
   ```

## Database Dump & Restore

```bash
# Dump the database (saves to dumps/ with timestamp)
make dump

# Restore from a dump file
make restore FILE=dumps/tedawards_20260211_120000.dump
```

## Configuration

Set environment variables in `.env`:
```env
DB_PATH=./tedawards.db          # SQLite database path (default: ./tedawards.db)
TED_DATA_DIR=./data              # Directory for downloaded packages (default: ./data)
LOG_LEVEL=INFO                   # Logging level (default: INFO)
```

## Database Schema

Key tables:
- `ted_documents` - Award notice metadata
- `contracting_bodies` - Organizations issuing contracts
- `contracts` - Procurement contracts
- `awards` - Award decisions and statistics
- `contractors` - Winning companies
- `award_contractors` - Award-contractor relationships

## Architecture

- **Parsers**: Automatically detects and processes multiple XML formats
  - `TedV2Parser` - TED 2.0 R2.0.7/R2.0.8/R2.0.9 formats (2011-2024)
  - `EFormsUBLParser` - eForms UBL ContractAwardNotice (2025+)
- **Database**: SQLite with comprehensive procurement schema (PostgreSQL also supported)
- **Scraper**: Downloads and processes TED packages by Official Journal issue number (sequential, not calendar-based)
- **CLI**: Separate commands for downloading and importing data

## Package Numbering

TED packages use **Official Journal (OJ S) issue numbers**, not calendar dates:
- Format: `{year}{issue_number:05d}` (e.g., `201100001` = issue 1 of 2011)
- Issues are sequential but skip weekends/holidays
- Typical year has ~250 issues (not 365 days)
- Scraper automatically handles gaps by stopping after 10 consecutive 404s

## Data Coverage

- **Time Range**: January 2011 to present (14+ years of XML-formatted data)
- **Data Quality**:
  - All key procurement data extracted accurately
  - Handles multiple XML formats and variations
  - Consistent processing across different archive dates
- **Format Support**: TED 2.0 (R2.0.7-R2.0.9) and eForms UBL
